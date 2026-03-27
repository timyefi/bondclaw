#!/usr/bin/env python3
"""
万科近 10 年年报/半年报纵向分析一键式 study runner。

流程：
1. 从 ChinaMoney 官方接口发现 2016-2025 的年报 / 半年报
2. 生成 discovery / download / task seed 产物
3. 调用 run_report_series.py 跑 scaffold-first 单案闭环
4. 如显式 formalize，则基于每份正式产物做二次阅读与 synthesis，输出 master reading ledger 与 master financial_output.xlsx；正式 analysis_report.md 需由 Codex 依据阅读结果另行写作
"""

import argparse
import collections
import datetime
import json
import math
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple

import xlsxwriter
import requests

from runtime_support import RuntimeConfigError, load_runtime_config, resolve_runtime_path, runtime_project_root


SCRIPT_DIR = Path(__file__).resolve().parent
REPO_ROOT = SCRIPT_DIR.parents[1]
CHINAMONEY_SCRIPT_DIR = REPO_ROOT / "chinamoney" / "scripts"
if str(CHINAMONEY_SCRIPT_DIR) not in sys.path:
    sys.path.insert(0, str(CHINAMONEY_SCRIPT_DIR))

from discover_reports import bootstrap_session, build_download_url, default_headers, fetch_finance_repo_page, now_iso as cm_now_iso  # type: ignore


REPORT_TYPES = [
    {"code": "4", "label": "年度报告", "kind": "annual"},
    {"code": "2", "label": "半年度报告", "kind": "semiannual"},
]

DEFAULT_YEAR_START = 2016
DEFAULT_YEAR_END = 2025
DEFAULT_ISSUER = "万科企业股份有限公司"
DEFAULT_ORG_NAME = "万科企业股份有限公司"
DEFAULT_STUDY_NAME = "vanke_longitudinal_study"
SERIES_MANIFEST_NAME = "series_manifest.json"
SERIES_RESULTS_NAME = "series_task_results.jsonl"
VANKE_OFFICIAL_CNAPI_BASE = "https://cnapi.vanke.com"
VANKE_OFFICIAL_WEB_BASE = "https://www.vanke.com"
VANKE_OFFICIAL_MANUAL_FALLBACKS = {
    (2020, "semiannual"): "https://www.vanke.com/upload/file/2020-08-31/dc5de537-6215-44b8-8c6d-21d1c1f211b6.pdf",
}


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def write_json(path: Path, payload: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False) + "\n")


def write_text(path: Path, text: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(text)


def sanitize_name(value: str) -> str:
    text = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").strip())
    text = text.strip("_")
    return text or "unknown"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="万科近 10 年年报/半年报纵向分析")
    parser.add_argument("--runtime-config", help="显式指定 runtime/runtime_config.json")
    parser.add_argument("--output-dir", help="输出目录；默认写入 runtime/state/tmp/vanke_longitudinal_study/<timestamp>")
    parser.add_argument("--year-start", type=int, default=DEFAULT_YEAR_START, help="起始年度，默认 2016")
    parser.add_argument("--year-end", type=int, default=DEFAULT_YEAR_END, help="结束年度，默认 2025")
    parser.add_argument("--download-timeout", type=int, default=120, help="单次下载超时秒数")
    parser.add_argument("--mineru-max-attempts", type=int, default=2, help="单份 PDF 的 MinerU 最大尝试次数")
    parser.add_argument("--resume-output-dir", action="store_true", help="若输出目录已存在，则复用而不是删除重跑")
    parser.add_argument("--prepare-only", action="store_true", help="仅生成 discovery 产物，不进入 series / 汇总")
    parser.add_argument("--series-only", action="store_true", help="跳过 discovery 生成步骤，直接复用已有 output-dir 中的 discovery 产物")
    parser.add_argument(
        "--postformalize-only",
        action="store_true",
        help="跳过 discovery / series 执行，只读取既有正式产物并生成 master 报告与 workbook",
    )
    parser.add_argument("--formalize", action="store_true", help="显式执行正式化并生成 master 报告与 workbook")
    parser.add_argument("--no-build-review-bundle", action="store_true", help="调用 series 时不构建 review bundle")
    return parser.parse_args()


def resolve_output_dir(runtime_config: Dict[str, Any], raw_output_dir: Optional[str]) -> Path:
    if raw_output_dir:
        return Path(raw_output_dir).resolve()
    tmp_root = resolve_runtime_path(runtime_config, "tmp_root")
    return (tmp_root / DEFAULT_STUDY_NAME / timestamp_slug()).resolve()


def ensure_under_project_root(path: Path, project_root: Path, label: str):
    try:
        path.relative_to(project_root)
    except ValueError as exc:
        raise SystemExit(f"{label} 必须位于 project_root 内: {path}") from exc


def report_type_meta(report_type_code: str) -> Dict[str, str]:
    for item in REPORT_TYPES:
        if item["code"] == str(report_type_code):
            return item
    raise KeyError(report_type_code)


def normalize_report_period(year: int, report_type_label: str) -> str:
    if report_type_label == "年度报告":
        return f"{year}年年度报告"
    if report_type_label == "半年度报告":
        return f"{year}年半年度报告"
    return f"{year}年{report_type_label}"


def normalize_vanke_official_kind(title: str) -> Optional[str]:
    text = str(title or "").strip()
    lowered = text.lower()
    if not text:
        return None
    if "摘要" in text or "summary" in lowered or "results announcement" in lowered:
        return None
    if (
        "半年度报告" in text
        or "中期" in text
        or "semi-annual report" in lowered
        or "interim report" in lowered
        or "six months ended" in lowered
    ):
        return "semiannual"
    if "年度报告" in text or "annual report" in lowered:
        return "annual"
    return None


def extract_report_year(text: str, *, fallback_year: Optional[int] = None) -> Optional[int]:
    source = str(text or "")
    for token in source.split():
        if len(token) >= 4 and token[:4].isdigit():
            return int(token[:4])
    match = None
    for chunk in re.findall(r"(20\d{2})", source):
        match = chunk
        break
    if match:
        return int(match)
    return fallback_year


def fetch_vanke_official_financial_feed(locale: str, page_index: int) -> List[Dict[str, Any]]:
    if locale in {"en", "Hant"}:
        api_prefix = f"/{locale}"
    else:
        api_prefix = ""
    if locale == "cn":
        referer = "https://www.vanke.com/mobile/investor/financial"
    elif locale == "en":
        referer = "https://vanke.com/en/mobile/investor/financial"
    else:
        referer = "https://www.vanke.com/mobile/investor/financial"
    url = f"{VANKE_OFFICIAL_CNAPI_BASE}{api_prefix}/api/News/GetInvestor?coid=61&pageIndex={page_index}&pageSize=10"
    response = requests.post(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
            "Accept": "application/json, text/plain, */*",
            "Referer": referer,
        },
        timeout=30,
    )
    response.raise_for_status()
    payload = response.json()
    return list(payload.get("data") or [])


def discover_vanke_official_fallbacks() -> Dict[str, Any]:
    candidates: Dict[Tuple[int, str], Dict[str, Any]] = {}
    feed_records: List[Dict[str, Any]] = []

    for locale in ("cn", "en"):
        for page_index in range(1, 6):
            try:
                items = fetch_vanke_official_financial_feed(locale, page_index)
            except Exception:
                break
            if not items:
                break
            for item in items:
                title = str(item.get("newsTitle", "")).strip()
                kind = normalize_vanke_official_kind(title)
                if not kind:
                    continue
                year = extract_report_year(
                    title,
                    fallback_year=extract_report_year(str(item.get("newsTime", "")).strip()),
                )
                if year is None or year < DEFAULT_YEAR_START or year > DEFAULT_YEAR_END:
                    continue
                image_path = str(item.get("image", "")).strip().replace("\\", "/")
                if not image_path:
                    continue
                official_download_url = image_path
                if official_download_url.startswith("/"):
                    official_download_url = VANKE_OFFICIAL_WEB_BASE + official_download_url
                feed_record = {
                    "locale": locale,
                    "page_index": page_index,
                    "year": year,
                    "report_kind": kind,
                    "report_type_label": "年度报告" if kind == "annual" else "半年度报告",
                    "title": title,
                    "news_time": str(item.get("newsTime", "")).strip(),
                    "official_download_url": official_download_url,
                    "news_id": item.get("newsID", ""),
                }
                feed_records.append(feed_record)
                candidates.setdefault((year, kind), feed_record)

    for (year, kind), url in VANKE_OFFICIAL_MANUAL_FALLBACKS.items():
        candidates[(year, kind)] = {
            "locale": "manual",
            "page_index": 0,
            "year": year,
            "report_kind": kind,
            "report_type_label": "年度报告" if kind == "annual" else "半年度报告",
            "title": f"{year} {'年度报告' if kind == 'annual' else '半年度报告'}",
            "news_time": "",
            "official_download_url": url,
            "news_id": "",
        }

    return {
        "generated_at": now_iso(),
        "source": "vanke_official",
        "records": feed_records,
        "candidates": {
            f"{year}_{kind}": record for (year, kind), record in sorted(candidates.items())
        },
    }


def extract_title_period(title: str) -> str:
    for marker in ("年度报告", "半年度报告", "半年度信息披露公告", "半年度财务报告信息披露公告"):
        if marker in title:
            return marker
    return title


def discover_vanke_reports(year_start: int, year_end: int) -> Dict[str, Any]:
    session = bootstrap_session()
    year_and_type = session.post(
        "https://www.chinamoney.com.cn/ags/ms/cm-u-notice-an/staYearAndType",
        headers=default_headers(),
        timeout=30,
    )
    year_and_type.raise_for_status()
    year_and_type_payload = year_and_type.json()

    candidates: List[Dict[str, Any]] = []
    missing_reports: List[Dict[str, Any]] = []

    for year in range(year_start, year_end + 1):
        for report_type in REPORT_TYPES:
            page = fetch_finance_repo_page(
                session,
                year=year,
                report_type=report_type["code"],
                org_name=DEFAULT_ORG_NAME,
                page_no=1,
                page_size=10,
            )
            records = page.get("records") or []
            if not records:
                missing_reports.append(
                    {
                        "year": year,
                        "report_type": report_type["code"],
                        "report_type_label": report_type["label"],
                        "report_kind": report_type["kind"],
                        "reason": "not_found_on_chinamoney",
                    }
                )
                continue

            record = records[0]
            content_id = str(record.get("contentId", "")).strip()
            title = str(record.get("title", "")).strip()
            release_date = str(record.get("releaseDate", "")).strip()
            draft_path = str(record.get("draftPath", "")).strip()
            download_url = build_download_url(content_id) if content_id else ""
            task_id = f"vanke_{year}_{report_type['kind']}"
            candidates.append(
                {
                    "task_id": task_id,
                    "issuer_name": DEFAULT_ISSUER,
                    "year": year,
                    "report_type": report_type["code"],
                    "report_type_label": report_type["label"],
                    "report_kind": report_type["kind"],
                    "report_period_label": normalize_report_period(year, report_type["label"]),
                    "content_id": content_id,
                    "title": title,
                    "release_date": release_date,
                    "draft_path": draft_path,
                    "draft_page_url": "https://www.chinamoney.com.cn" + draft_path if draft_path else "",
                    "download_url": download_url,
                    "effective_download_url": download_url,
                    "content_length": int(record.get("attSize") or 0),
                    "channel_path": str(record.get("channelPath", "")).strip(),
                    "suffix": str(record.get("suffix", "")).strip(),
                    "attachment_count": int(record.get("attSize") or 0),
                    "raw_record": record,
                }
            )

    official_fallback_manifest = discover_vanke_official_fallbacks()
    official_candidates = official_fallback_manifest.get("candidates") or {}
    for candidate in candidates:
        official_key = f"{candidate['year']}_{candidate['report_kind']}"
        official = official_candidates.get(official_key, {})
        candidate["official_source"] = str(official.get("locale", "")).strip()
        candidate["official_download_url"] = str(official.get("official_download_url", "")).strip()
        candidate["official_title"] = str(official.get("title", "")).strip()

    coverage = {
        "year_start": year_start,
        "year_end": year_end,
        "planned_report_count": (year_end - year_start + 1) * len(REPORT_TYPES),
        "discovered_report_count": len(candidates),
        "missing_report_count": len(missing_reports),
        "annual_report_count": sum(1 for item in candidates if item["report_kind"] == "annual"),
        "semiannual_report_count": sum(1 for item in candidates if item["report_kind"] == "semiannual"),
    }

    return {
        "generated_at": now_iso(),
        "issuer_name": DEFAULT_ISSUER,
        "year_and_type_head": {
            "status_code": year_and_type.status_code,
            "requested_at": cm_now_iso(),
        },
        "year_and_type_data": year_and_type_payload.get("data") or {},
        "candidates": candidates,
        "missing_reports": missing_reports,
        "coverage": coverage,
        "official_fallback_manifest": official_fallback_manifest,
    }


def make_download_task(candidate: Dict[str, Any]) -> Dict[str, Any]:
    filename = f"{candidate['report_period_label']}.pdf"
    safe_name = "".join(ch if ch.isalnum() or ch in "._-()" else "_" for ch in filename).strip("._") or f"{candidate['task_id']}.pdf"
    return {
        "name": f"{candidate['issuer_name']}{candidate['report_period_label']}",
        "url": candidate["download_url"],
        "output_path": str(Path("downloads") / candidate["task_id"] / safe_name),
        "retries": 1,
        "source": {
            "content_id": candidate["content_id"],
            "draft_page_url": candidate["draft_page_url"],
            "release_date": candidate["release_date"],
            "official_source": candidate.get("official_source", ""),
            "official_download_url": candidate.get("official_download_url", ""),
            "report_type": candidate["report_type_label"],
            "report_type_code": candidate["report_type"],
            "report_kind": candidate["report_kind"],
        },
    }


def make_task_seed(candidate: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    pdf_name = f"{candidate['report_period_label']}.pdf"
    safe_pdf_name = "".join(ch if ch.isalnum() or ch in "._-()" else "_" for ch in pdf_name).strip("._") or f"{candidate['task_id']}.pdf"
    source_pdf = output_dir / "downloads" / candidate["task_id"] / safe_pdf_name
    return {
        "task_id": candidate["task_id"],
        "issuer": candidate["issuer_name"],
        "year": candidate["year"],
        "report_type": candidate["report_type_label"],
        "report_type_code": candidate["report_type"],
        "report_type_label": candidate["report_type_label"],
        "report_kind": candidate["report_kind"],
        "report_period_label": candidate["report_period_label"],
        "source_pdf": str(source_pdf),
        "md_path": str(output_dir / "markdown" / candidate["task_id"] / f"{candidate['task_id']}.md"),
        "notes_workfile": str(output_dir / "notes_workfiles" / f"{candidate['task_id']}.json"),
        "run_dir": str(output_dir / "runs" / candidate["task_id"]),
        "selection_bucket": candidate["report_kind"],
        "selection_reason": f"report_type={candidate['report_type_label']}; release_date={candidate['release_date']}",
        "tags": ["vanke", "longitudinal", candidate["report_kind"], candidate["report_type_label"]],
        "source": {
            "content_id": candidate["content_id"],
            "title": candidate["title"],
            "draft_page_url": candidate["draft_page_url"],
            "download_url": candidate["download_url"],
            "effective_download_url": candidate["effective_download_url"],
            "official_source": "",
            "official_download_url": "",
            "release_date": candidate["release_date"],
            "content_length": candidate["content_length"],
            "report_type": candidate["report_type_label"],
            "report_type_code": candidate["report_type"],
            "report_kind": candidate["report_kind"],
        },
    }


def build_selection_manifest(discovery: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    selected_candidates = []
    for candidate in discovery["candidates"]:
        selected_candidates.append(
            {
                "task_id": candidate["task_id"],
                "issuer_name": candidate["issuer_name"],
                "year": candidate["year"],
                "report_type": candidate["report_type"],
                "report_type_label": candidate["report_type_label"],
                "report_kind": candidate["report_kind"],
                "content_id": candidate["content_id"],
                "title": candidate["title"],
                "release_date": candidate["release_date"],
                "draft_page_url": candidate["draft_page_url"],
                "download_url": candidate["download_url"],
                "effective_download_url": candidate["effective_download_url"],
                "content_length": candidate["content_length"],
                "selection_reason": f"{candidate['report_type_label']} | {candidate['release_date']}",
            }
        )

    return {
        "generated_at": now_iso(),
        "out_dir": str(output_dir),
        "policy": {
            "issuer_name": DEFAULT_ISSUER,
            "year_start": discovery["coverage"]["year_start"],
            "year_end": discovery["coverage"]["year_end"],
            "source_pool": {
                "channel": "ChinaMoney financeRepo",
                "org_name": DEFAULT_ORG_NAME,
                "report_types": [
                    {"code": item["code"], "label": item["label"]} for item in REPORT_TYPES
                ],
            },
            "notes": [
                "2025 年度报告目前在 ChinaMoney 上未发现，保留为真实缺口。",
                "半年报使用 type=2，年度报告使用 type=4。",
                "官方发行人站点作为补充下载源，用于 ChinaMoney 直接下载失败时回退。",
            ],
        },
        "candidate_pool_summary": discovery["coverage"],
        "selected_candidates": selected_candidates,
        "reserve_candidates": [],
        "missing_reports": discovery["missing_reports"],
        "official_fallback_manifest": discovery.get("official_fallback_manifest", {}),
    }


def build_download_config(discovery: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    tasks = [make_download_task(candidate) for candidate in discovery["candidates"]]
    return {
        "generated_at": now_iso(),
        "output_dir": str(output_dir),
        "tasks": tasks,
    }


def build_task_seed_list(discovery: Dict[str, Any], output_dir: Path) -> Dict[str, Any]:
    tasks = [make_task_seed(candidate, output_dir) for candidate in discovery["candidates"]]
    return {
        "generated_at": now_iso(),
        "task_count": len(tasks),
        "tasks": tasks,
    }


def build_run_command(python_executable: str, series_script: Path, discovery_dir: Path, output_dir: Path, args: argparse.Namespace) -> List[str]:
    command = [
        python_executable,
        str(series_script),
        "--p4-dir",
        str(discovery_dir),
        "--output-dir",
        str(output_dir),
        "--download-timeout",
        str(args.download_timeout),
        "--mineru-max-attempts",
        str(args.mineru_max_attempts),
    ]
    if args.resume_output_dir:
        command.append("--resume-output-dir")
    if args.formalize:
        command.append("--formalize")
    if args.no_build_review_bundle:
        command.append("--no-build-review-bundle")
    return command


def metric_value_to_string(value: Any) -> str:
    if value is None:
        return ""
    if isinstance(value, (dict, list, tuple, set)):
        return json.dumps(value, ensure_ascii=False)
    if isinstance(value, float):
        if math.isfinite(value):
            if float(value).is_integer():
                return str(int(value))
            return f"{value:.4f}".rstrip("0").rstrip(".")
        return ""
    return str(value)


def normalize_numeric(value: Any) -> Optional[float]:
    if isinstance(value, bool):
        return None
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        text = value.strip().replace(",", "")
        if not text:
            return None
        try:
            return float(text)
        except ValueError:
            return None
    return None


def period_sort_key(report_type_label: str, report_period_label: str) -> Tuple[int, int, int]:
    year_text = "".join(ch for ch in report_period_label if ch.isdigit())[:4]
    year = int(year_text) if year_text else 0
    if report_type_label == "年度报告":
        return (0, year, 0)
    if report_type_label == "半年度报告":
        return (1, year, 0)
    return (2, year, 0)


def collect_series_records(series_dir: Path, discovery: Dict[str, Any]) -> Dict[str, Any]:
    results_path = series_dir / SERIES_RESULTS_NAME
    series_manifest_path = series_dir / SERIES_MANIFEST_NAME
    results = read_jsonl(results_path) if results_path.exists() else []
    series_manifest = read_json(series_manifest_path) if series_manifest_path.exists() else {}

    seed_by_task_id = {task["task_id"]: task for task in discovery["task_seed_list"]["tasks"]}
    report_entries: List[Dict[str, Any]] = []
    reading_digest_rows: List[Dict[str, Any]] = []
    topic_rows: List[Dict[str, Any]] = []
    risk_rows: List[Dict[str, Any]] = []
    metric_rows: List[Dict[str, Any]] = []
    evidence_rows: List[Dict[str, Any]] = []
    top_risk_counter = collections.Counter()
    top_metric_counter = collections.Counter()

    for item in results:
        task_id = str(item.get("task_id", "")).strip()
        seed = seed_by_task_id.get(task_id, {})
        task_run_dir = Path(str(item.get("task_run_dir", ""))).resolve() if item.get("task_run_dir") else Path("")
        status = str(item.get("status", "failed"))
        soul_payload_path = task_run_dir / "soul_export_payload.json"
        final_data_path = task_run_dir / "final_data.json"
        analysis_report_path = task_run_dir / "analysis_report.md"
        run_manifest_path = task_run_dir / "run_manifest.json"
        soul_payload: Dict[str, Any] = {}
        final_data: Dict[str, Any] = {}
        run_manifest: Dict[str, Any] = {}
        if soul_payload_path.exists():
            soul_payload = read_json(soul_payload_path)
        if final_data_path.exists():
            final_data = read_json(final_data_path)
        if run_manifest_path.exists():
            run_manifest = read_json(run_manifest_path)

        entity = soul_payload.get("entity_profile") or {}
        overview = soul_payload.get("overview") or {}
        kpi_dashboard = soul_payload.get("kpi_dashboard") or {}
        financial_summary = soul_payload.get("financial_summary") or {}
        debt_profile = soul_payload.get("debt_profile") or {}
        liquidity = soul_payload.get("liquidity_and_covenants") or {}
        evidence_index = soul_payload.get("evidence_index") or []
        reading_digest = build_reading_digest(item, seed, run_manifest, final_data, soul_payload)

        if status == "success":
            reading_digest_rows.append(reading_digest)
            for risk in overview.get("key_risks") or []:
                top_risk_counter[str(risk.get("risk_code", "")) or "unknown"] += 1
                risk_rows.append(
                    {
                        "task_id": task_id,
                        "issuer": item.get("issuer", ""),
                        "year": item.get("year", ""),
                        "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
                        "report_period_label": seed.get("report_period_label", ""),
                        "risk_code": risk.get("risk_code", ""),
                        "label": risk.get("label", ""),
                        "risk_level": risk.get("risk_level", ""),
                        "description": risk.get("description", ""),
                        "evidence_refs": ", ".join(risk.get("evidence_refs") or []),
                    }
                )
            for section in kpi_dashboard.get("sections") or []:
                for metric in section.get("metrics") or []:
                    top_metric_counter[str(metric.get("metric_code", "")) or "unknown"] += 1
                    metric_rows.append(
                        {
                            "task_id": task_id,
                            "issuer": item.get("issuer", ""),
                            "year": item.get("year", ""),
                            "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
                            "report_period_label": seed.get("report_period_label", ""),
                            "category": section.get("category", ""),
                            "metric_code": metric.get("metric_code", ""),
                            "label": metric.get("label", ""),
                            "value": metric.get("value", None),
                            "value_text": metric_value_to_string(metric.get("value")),
                            "unit": metric.get("unit", ""),
                            "period": metric.get("period", ""),
                            "comparison": metric.get("comparison", ""),
                            "benchmark": metric.get("benchmark", ""),
                            "risk_level": metric.get("risk_level", ""),
                            "source_status": metric.get("source_status", ""),
                            "evidence_refs": ", ".join(metric.get("evidence_refs") or []),
                            "analysis_report": str(analysis_report_path),
                        }
                    )
            topic_rows.extend(build_topic_rollup_rows(item, seed, final_data))
            for entry in evidence_index:
                evidence_rows.append(
                    {
                        "task_id": task_id,
                        "issuer": item.get("issuer", ""),
                        "year": item.get("year", ""),
                        "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
                        "evidence_id": entry.get("evidence_id", ""),
                        "field_path": entry.get("field_path", ""),
                        "sheet_name": entry.get("sheet_name", ""),
                        "excerpt": entry.get("excerpt", ""),
                        "source_document": entry.get("source_document", ""),
                        "chapter_no": entry.get("chapter_no", ""),
                        "chapter_title": entry.get("chapter_title", ""),
                        "note_no": entry.get("note_no", ""),
                        "line_span": entry.get("line_span", ""),
                        "confidence": entry.get("confidence", ""),
                }
            )
        else:
            reading_digest_rows.append(reading_digest)

        report_entries.append(
            {
                "task_id": task_id,
                "issuer": item.get("issuer", seed.get("issuer", DEFAULT_ISSUER)),
                "year": item.get("year", seed.get("year", "")),
                "report_type": item.get("report_type", seed.get("report_type", "")),
                "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
                "report_period_label": item.get("report_period_label", seed.get("report_period_label", "")),
                "status": status,
                "download_status": item.get("download_status", ""),
                "analysis_status": item.get("analysis_status", ""),
                "failure_stage": item.get("failure_stage", ""),
                "failure_reason": item.get("failure_reason", ""),
                "batch_run_dir": item.get("batch_run_dir", ""),
                "task_run_dir": item.get("task_run_dir", ""),
                "analysis_report": item.get("analysis_report", str(analysis_report_path) if analysis_report_path.exists() else ""),
                "final_data": item.get("final_data", str(final_data_path) if final_data_path.exists() else ""),
                "soul_export_payload": item.get("soul_export_payload", str(soul_payload_path) if soul_payload_path.exists() else ""),
                "financial_output": item.get("financial_output", str(task_run_dir / "financial_output.xlsx") if task_run_dir.exists() else ""),
                "content_id": str(seed.get("source", {}).get("content_id", "")),
                "release_date": str(seed.get("source", {}).get("release_date", "")),
                "content_length": seed.get("source", {}).get("content_length", ""),
                "kpi_metric_count": sum(len(section.get("metrics") or []) for section in kpi_dashboard.get("sections") or []),
                "evidence_count": len(evidence_index),
                "top_risks": "; ".join(
                    f"{risk.get('risk_code', '')}:{risk.get('risk_level', '')}"
                    for risk in (overview.get("key_risks") or [])
                ),
                "key_conclusions": " | ".join(final_data.get("key_conclusions") or []),
                "coverage_note": (financial_summary.get("coverage_note") or ""),
                "run_manifest_status": run_manifest.get("status", ""),
                "chapter_total": reading_digest.get("chapter_total", 0),
                "topic_count": reading_digest.get("topic_count", 0),
                "top_topics": reading_digest.get("top_topics_text", ""),
                "top_risks": reading_digest.get("top_risks_text", ""),
                "reading_note": reading_digest.get("reading_note", ""),
            }
        )

    report_entries.sort(
        key=lambda item: period_sort_key(str(item.get("report_type_label", "")), str(item.get("report_period_label", "")))
    )
    metric_rows.sort(
        key=lambda item: (
            item["report_type_label"],
            str(item["year"]),
            item["category"],
            item["metric_code"],
        )
    )
    evidence_rows.sort(
        key=lambda item: (
            str(item["year"]),
            item["report_type_label"],
            item["evidence_id"],
        )
    )
    topic_rows.sort(
        key=lambda item: (
            period_sort_key(str(item.get("report_type_label", "")), str(item.get("report_period_label", ""))),
            -int(item.get("chapter_count", 0) or 0),
            str(item.get("topic_key", "")),
        )
    )
    risk_rows.sort(
        key=lambda item: (
            period_sort_key(str(item.get("report_type_label", "")), str(item.get("report_period_label", ""))),
            str(item.get("risk_level", "")),
            str(item.get("risk_code", "")),
        )
    )
    report_type_counts = collections.Counter(
        item["report_type_label"]
        for item in report_entries
        if item.get("status") == "success" and item.get("report_type_label")
    )

    return {
        "series_manifest": series_manifest,
        "results": results,
        "reports": report_entries,
        "reading_digest_rows": reading_digest_rows,
        "topic_rows": topic_rows,
        "risk_rows": risk_rows,
        "metric_rows": metric_rows,
        "evidence_rows": evidence_rows,
        "top_risk_counter": top_risk_counter,
        "top_metric_counter": top_metric_counter,
        "report_type_counts": report_type_counts,
    }


def severity_sort_key(value: Any) -> int:
    order = {
        "high": 0,
        "medium": 1,
        "low": 2,
        "unknown": 3,
        "": 4,
    }
    return order.get(str(value).strip().lower(), 5)


def extract_chapter_total(run_manifest: Dict[str, Any], final_data: Dict[str, Any], soul_payload: Dict[str, Any]) -> int:
    counts = run_manifest.get("counts") or {}
    chapter_total = counts.get("chapter_records")
    if isinstance(chapter_total, int) and chapter_total > 0:
        return chapter_total
    for text in final_data.get("key_conclusions") or []:
        match = re.search(r"(\d+)\s*条", str(text))
        if match:
            return int(match.group(1))
    for text in (soul_payload.get("overview") or {}).get("executive_summary") or []:
        match = re.search(r"(\d+)\s*条", str(text))
        if match:
            return int(match.group(1))
    return 0


def summarize_topic_payload(topic_key: str, payload: Dict[str, Any]) -> Dict[str, Any]:
    attributes = payload.get("attributes") or {}
    chapter_count = attributes.get("chapter_count")
    risk_signals = payload.get("extensions", {}).get("risk_signals") or []
    summary = str(payload.get("summary") or "").replace("\n", " ").strip()
    if len(summary) > 160:
        summary = summary[:157] + "..."
    return {
        "topic_key": topic_key,
        "topic_display": topic_key.replace("_", " ") if "_" in topic_key and not any("\u4e00" <= ch <= "\u9fff" for ch in topic_key) else topic_key,
        "chapter_count": int(chapter_count or 0),
        "risk_signal_count": len(risk_signals),
        "summary": summary,
    }


def build_topic_rollup_rows(item: Dict[str, Any], seed: Dict[str, Any], final_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    topic_items = []
    for topic_key, payload in (final_data.get("topic_results") or {}).items():
        topic_items.append(summarize_topic_payload(topic_key, payload or {}))
    topic_items.sort(key=lambda row: (-row["chapter_count"], -row["risk_signal_count"], row["topic_key"]))
    for row in topic_items[:8]:
        rows.append(
            {
                "task_id": item.get("task_id", ""),
                "issuer": item.get("issuer", ""),
                "year": item.get("year", ""),
                "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
                "report_period_label": seed.get("report_period_label", ""),
                **row,
            }
        )
    return rows


def build_reading_digest(
    item: Dict[str, Any],
    seed: Dict[str, Any],
    run_manifest: Dict[str, Any],
    final_data: Dict[str, Any],
    soul_payload: Dict[str, Any],
) -> Dict[str, Any]:
    entity_profile = soul_payload.get("entity_profile") or {}
    overview = soul_payload.get("overview") or {}
    key_conclusions = final_data.get("key_conclusions") or []
    raw_risks = overview.get("key_risks") or []
    risks = sorted(
        raw_risks,
        key=lambda row: (
            severity_sort_key(row.get("risk_level")),
            str(row.get("risk_code", "")),
        ),
    )
    topic_rows = []
    for topic_key, payload in (final_data.get("topic_results") or {}).items():
        topic_rows.append(summarize_topic_payload(topic_key, payload or {}))
    topic_rows.sort(key=lambda row: (-row["chapter_count"], -row["risk_signal_count"], row["topic_key"]))
    chapter_total = extract_chapter_total(run_manifest, final_data, soul_payload)
    top_topics = topic_rows[:5]
    top_risks = risks[:5]
    top_topic_text = "；".join(f"`{row['topic_display']}`({row['chapter_count']})" for row in top_topics) if top_topics else "暂无稳定主题"
    top_risk_text = "；".join(
        f"`{risk.get('risk_code', '')}`/{risk.get('risk_level', '')}"
        for risk in top_risks
        if risk.get("risk_code")
    ) or "暂无稳定风险"
    reading_note = (
        f"{item.get('report_period_label', seed.get('report_period_label', ''))}："
        f"总附注 {chapter_total} 章，阅读重心落在 {top_topic_text}；"
        f"高频风险聚焦 {top_risk_text}。"
    )
    if key_conclusions:
        reading_note = reading_note + f" 结论起点：{str(key_conclusions[0]).strip()}"
    return {
        "task_id": item.get("task_id", ""),
        "issuer": item.get("issuer", entity_profile.get("company_name", DEFAULT_ISSUER)),
        "year": item.get("year", entity_profile.get("report_period", "")),
        "report_type_label": item.get("report_type_label", seed.get("report_type_label", "")),
        "report_period_label": item.get("report_period_label", seed.get("report_period_label", "")),
        "report_type": item.get("report_type", ""),
        "status": item.get("status", ""),
        "chapter_total": chapter_total,
        "topic_count": len(final_data.get("topic_results") or {}),
        "top_topics_text": top_topic_text,
        "top_risks_text": top_risk_text,
        "reading_note": reading_note,
        "key_conclusions": " | ".join(str(text).strip() for text in key_conclusions[:3] if text),
        "analysis_report": item.get("analysis_report", ""),
        "final_data": item.get("final_data", ""),
        "soul_export_payload": item.get("soul_export_payload", ""),
        "financial_output": item.get("financial_output", ""),
        "source_pdf": item.get("source_pdf", ""),
        "run_manifest": item.get("run_manifest", ""),
    }


def infer_trend(rows: List[Dict[str, Any]]) -> Dict[str, Any]:
    numeric_points: List[Tuple[Tuple[int, int, int], float, str]] = []
    for row in rows:
        numeric_value = normalize_numeric(row.get("value"))
        if numeric_value is None:
            continue
        numeric_points.append(
            (
                period_sort_key(str(row.get("report_type_label", "")), str(row.get("report_period_label", ""))),
                numeric_value,
                str(row.get("report_period_label", "")),
            )
        )
    numeric_points.sort(key=lambda item: item[0])
    if len(numeric_points) < 2:
        return {"direction": "insufficient", "points": numeric_points}
    first = numeric_points[0][1]
    last = numeric_points[-1][1]
    if first == 0:
        ratio = None
    else:
        ratio = last / first
    if ratio is not None and ratio >= 1.25:
        direction = "up"
    elif ratio is not None and ratio <= 0.8:
        direction = "down"
    else:
        direction = "flat"
    return {
        "direction": direction,
        "ratio": ratio,
        "first": numeric_points[0],
        "last": numeric_points[-1],
        "points": numeric_points,
    }


def format_metric_cells(row: Dict[str, Any]) -> Tuple[Any, str]:
    value = row.get("value")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return value, "number"
    if value is None or value == "":
        return "", "text"
    return metric_value_to_string(value), "text"


def build_report_markdown(summary: Dict[str, Any]) -> str:
    reports = summary["reports"]
    reading_rows = summary["reading_digest_rows"]
    topic_rows = summary["topic_rows"]
    risk_rows = summary["risk_rows"]
    metric_rows = summary["metric_rows"]
    report_type_counts = summary.get("report_type_counts", {})
    series_manifest = summary["series_manifest"]
    coverage_info = summary.get("coverage", {})
    missing_report_count = summary.get("missing_report_count", 0)

    success_count = sum(1 for item in reports if item["status"] == "success")
    coverage = series_manifest.get("summary", {})
    annual_readings = [row for row in reading_rows if row["report_type_label"] == "年度报告" and row["status"] == "success"]
    semiannual_readings = [row for row in reading_rows if row["report_type_label"] == "半年度报告" and row["status"] == "success"]

    risk_counter = collections.Counter()
    for row in risk_rows:
        if row.get("risk_code"):
            risk_counter[row["risk_code"]] += 1

    topic_counter = collections.Counter()
    for row in topic_rows:
        if row.get("topic_key"):
            topic_counter[row["topic_key"]] += 1

    reading_lines = []
    for row in reading_rows:
        reading_lines.append(
            f"### {row['report_period_label']}\n"
            f"- 状态：{row['status']}\n"
            f"- 总附注章数：{row['chapter_total']}\n"
            f"- 主题重心：{row['top_topics_text']}\n"
            f"- 风险标签：{row['top_risks_text']}\n"
            f"- 阅读摘要：{row['reading_note']}\n"
            f"- 产物：`analysis_report.md` / `final_data.json` / `soul_export_payload.json` / `financial_output.xlsx`\n"
        )

    risk_lines = []
    for risk_code, count in risk_counter.most_common(8):
        risk_lines.append(f"- `{risk_code}`: {count} 份报告")
    if not risk_lines:
        risk_lines = ["- 暂无可归纳的高频风险标签"]

    topic_lines = []
    for topic_key, count in topic_counter.most_common(8):
        topic_lines.append(f"- `{topic_key}`: {count} 次出现在各报告的重点阅读位")
    if not topic_lines:
        topic_lines = ["- 暂无可归纳的高频主题"]

    annual_total_chapters = [row["chapter_total"] for row in annual_readings]
    semiannual_total_chapters = [row["chapter_total"] for row in semiannual_readings]
    annual_avg = (sum(annual_total_chapters) / len(annual_total_chapters)) if annual_total_chapters else 0
    semiannual_avg = (sum(semiannual_total_chapters) / len(semiannual_total_chapters)) if semiannual_total_chapters else 0

    report_lines = [
        "# 万科近 10 年年报/半年报后续阅读分析",
        "",
        "## 方法",
        f"- 阅读对象：既有 19 份正式输出，而不是重新回到原始 PDF 解析。",
        f"- 阅读顺序：逐份读取 `analysis_report.md`、`final_data.json`、`soul_export_payload.json`，再回看对应 `financial_output.xlsx`。",
        f"- 目标：先形成每份报告的阅读摘要，再做横向 synthesis，最后才考虑知识净化。",
        "",
        "## 覆盖情况",
        f"- 覆盖窗口：{coverage_info.get('year_start', 2016)}-{coverage_info.get('year_end', 2025)} 自然年窗口",
        f"- 正式报告数：{success_count}/{len(reports)}",
        f"- 发现缺口：{missing_report_count} 份缺失，2025 年报当前未发现",
        f"- 年度样本数：{report_type_counts.get('年度报告', 0)}",
        f"- 半年度样本数：{report_type_counts.get('半年度报告', 0)}",
        f"- 年度总附注平均章数：{annual_avg:.1f}",
        f"- 半年度总附注平均章数：{semiannual_avg:.1f}",
        "",
        "## 高频风险",
        *risk_lines,
        "",
        "## 高频主题",
        *topic_lines,
        "",
        "## 逐报告阅读",
        *reading_lines,
        "",
        "## 年度样本观感",
    ]

    if annual_readings:
        for row in annual_readings[:5]:
            report_lines.append(
                f"- {row['report_period_label']}: {row['reading_note']}"
            )
    else:
        report_lines.append("- 暂无可用年度样本")

    report_lines.extend([
        "",
        "## 半年度样本观感",
    ])
    if semiannual_readings:
        for row in semiannual_readings[:5]:
            report_lines.append(
                f"- {row['report_period_label']}: {row['reading_note']}"
            )
    else:
        report_lines.append("- 暂无可用半年度样本")

    report_lines.extend([
        "",
        "## 报告清单",
    ])
    for row in reports:
        report_lines.append(
            f"- {row['report_period_label']} | {row['status']} | {row['analysis_report']} | {row['financial_output']}"
        )

    return "\n".join(report_lines) + "\n"


def build_workbook(output_path: Path, summary: Dict[str, Any]):
    output_path.parent.mkdir(parents=True, exist_ok=True)
    workbook = xlsxwriter.Workbook(str(output_path))
    formats = {
        "title": workbook.add_format({
            "bold": True,
            "font_size": 16,
            "font_color": "#FFFFFF",
            "bg_color": "#16324F",
            "align": "left",
            "valign": "vcenter",
        }),
        "section": workbook.add_format({
            "bold": True,
            "font_color": "#16324F",
            "bg_color": "#D9E2F3",
            "border": 1,
        }),
        "header": workbook.add_format({
            "bold": True,
            "font_color": "#FFFFFF",
            "bg_color": "#1F4E78",
            "border": 1,
            "align": "center",
            "valign": "vcenter",
        }),
        "text": workbook.add_format({"text_wrap": True, "valign": "top", "border": 1}),
        "muted": workbook.add_format({"text_wrap": True, "valign": "top", "border": 1, "font_color": "#6B7280"}),
        "number": workbook.add_format({"border": 1, "num_format": '#,##0.00;[Red](#,##0.00);-'}),
        "integer": workbook.add_format({"border": 1, "num_format": '#,##0;[Red](#,##0);-'}),
        "note": workbook.add_format({"italic": True, "font_color": "#4B5563", "text_wrap": True}),
        "risk_high": workbook.add_format({"border": 1, "bg_color": "#FDE9D9", "font_color": "#9C0006"}),
        "risk_medium": workbook.add_format({"border": 1, "bg_color": "#FFF2CC", "font_color": "#7F6000"}),
        "risk_low": workbook.add_format({"border": 1, "bg_color": "#E2F0D9", "font_color": "#385723"}),
    }

    reports = summary["reports"]
    reading_rows = summary["reading_digest_rows"]
    topic_rows = summary["topic_rows"]
    risk_rows = summary["risk_rows"]
    evidence_rows = summary["evidence_rows"]
    metric_rows = summary["metric_rows"]
    success_count = sum(1 for row in reports if row["status"] == "success")
    annual_rows = [row for row in reading_rows if row["report_type_label"] == "年度报告" and row["status"] == "success"]
    semiannual_rows = [row for row in reading_rows if row["report_type_label"] == "半年度报告" and row["status"] == "success"]
    annual_avg_chapters = (
        sum(row["chapter_total"] for row in annual_rows) / len(annual_rows)
        if annual_rows
        else 0
    )
    semiannual_avg_chapters = (
        sum(row["chapter_total"] for row in semiannual_rows) / len(semiannual_rows)
        if semiannual_rows
        else 0
    )

    overview_sheet = workbook.add_worksheet("00_overview")
    overview_sheet.hide_gridlines(2)
    overview_sheet.freeze_panes(4, 0)
    overview_sheet.set_column("A:A", 20)
    overview_sheet.set_column("B:B", 16)
    overview_sheet.set_column("C:C", 18)
    overview_sheet.set_column("D:D", 18)
    overview_sheet.set_column("E:E", 18)
    overview_sheet.set_column("F:F", 18)
    overview_sheet.set_column("G:G", 18)
    overview_sheet.set_column("H:H", 60)
    overview_sheet.merge_range(0, 0, 0, 7, "万科既有正式研报的二次阅读 synthesis", formats["title"])
    overview_sheet.write(1, 0, "逐份读取 formal outputs 后再生成总报告与总 Excel", formats["note"])
    overview_sheet.write_row(2, 0, ["指标", "数值", "说明"], formats["header"])
    overview_rows = [
        ("覆盖报告数", len(reports), "19 份正式输出"),
        ("成功阅读数", success_count, "成功读取并纳入 synthesis 的报告"),
        ("年度样本数", len(annual_rows), "逐份正式产物阅读"),
        ("半年度样本数", len(semiannual_rows), "逐份正式产物阅读"),
        ("年度平均附注章数", round(annual_avg_chapters, 1), "按总附注章数统计"),
        ("半年度平均附注章数", round(semiannual_avg_chapters, 1), "按总附注章数统计"),
        ("缺失年报", summary.get("missing_report_count", 0), "2025 年报保持为真实缺口"),
    ]
    row = 3
    for label, value, note in overview_rows:
        overview_sheet.write(row, 0, label, formats["section"])
        if isinstance(value, (int, float)) and not isinstance(value, bool):
            overview_sheet.write(row, 1, value, formats["number"] if isinstance(value, float) and not float(value).is_integer() else formats["integer"])
        else:
            overview_sheet.write(row, 1, value, formats["text"])
        overview_sheet.write(row, 2, note, formats["text"])
        row += 1

    overview_sheet.write(row + 1, 0, "高频风险", formats["section"])
    overview_sheet.write(row + 1, 1, "报告数", formats["section"])
    overview_sheet.write(row + 1, 2, "观察", formats["section"])
    risk_counter = summary["top_risk_counter"]
    risk_row = row + 2
    for risk_code, count in risk_counter.most_common(8):
        overview_sheet.write(risk_row, 0, risk_code, formats["text"])
        overview_sheet.write(risk_row, 1, count, formats["integer"])
        overview_sheet.write(risk_row, 2, "来自各份正式输出的 `overview.key_risks`", formats["text"])
        risk_row += 1

    digest_sheet = workbook.add_worksheet("01_report_digest")
    digest_sheet.hide_gridlines(2)
    digest_sheet.freeze_panes(1, 0)
    digest_sheet.set_column("A:A", 18)
    digest_sheet.set_column("B:B", 14)
    digest_sheet.set_column("C:C", 14)
    digest_sheet.set_column("D:D", 12)
    digest_sheet.set_column("E:E", 12)
    digest_sheet.set_column("F:F", 60)
    digest_sheet.set_column("G:G", 60)
    digest_sheet.set_column("H:H", 90)
    digest_sheet.set_column("I:I", 60)
    digest_sheet.set_column("J:J", 60)
    digest_sheet.set_column("K:K", 60)
    digest_sheet.write_row(0, 0, [
        "task_id",
        "report_period",
        "report_type",
        "status",
        "chapter_total",
        "topic_count",
        "top_topics",
        "top_risks",
        "reading_note",
        "analysis_report",
        "financial_output",
    ], formats["header"])
    row = 1
    for report in reading_rows:
        digest_sheet.write(row, 0, report["task_id"], formats["text"])
        digest_sheet.write(row, 1, report["report_period_label"], formats["text"])
        digest_sheet.write(row, 2, report["report_type_label"], formats["text"])
        digest_sheet.write(row, 3, report["status"], formats["text"])
        digest_sheet.write(row, 4, report["chapter_total"], formats["integer"])
        digest_sheet.write(row, 5, report["topic_count"], formats["integer"])
        digest_sheet.write(row, 6, report["top_topics_text"], formats["text"])
        digest_sheet.write(row, 7, report["top_risks_text"], formats["text"])
        digest_sheet.write(row, 8, report["reading_note"], formats["text"])
        digest_sheet.write(row, 9, report["analysis_report"], formats["text"])
        digest_sheet.write(row, 10, report["financial_output"], formats["text"])
        row += 1

    risk_sheet = workbook.add_worksheet("02_risk_rollup")
    risk_sheet.hide_gridlines(2)
    risk_sheet.freeze_panes(1, 0)
    risk_sheet.set_column("A:A", 18)
    risk_sheet.set_column("B:B", 18)
    risk_sheet.set_column("C:C", 18)
    risk_sheet.set_column("D:D", 18)
    risk_sheet.set_column("E:E", 18)
    risk_sheet.set_column("F:F", 60)
    risk_sheet.set_column("G:G", 60)
    risk_sheet.write_row(0, 0, [
        "task_id",
        "report_period",
        "report_type",
        "risk_code",
        "risk_level",
        "label",
        "description",
        "evidence_refs",
    ], formats["header"])
    row = 1
    for item in risk_rows:
        risk_sheet.write(row, 0, item["task_id"], formats["text"])
        risk_sheet.write(row, 1, item["report_period_label"], formats["text"])
        risk_sheet.write(row, 2, item["report_type_label"], formats["text"])
        risk_sheet.write(row, 3, item["risk_code"], formats["text"])
        risk_format = formats["risk_high"]
        if str(item.get("risk_level", "")).lower() == "medium":
            risk_format = formats["risk_medium"]
        elif str(item.get("risk_level", "")).lower() == "low":
            risk_format = formats["risk_low"]
        risk_sheet.write(row, 4, item["risk_level"], risk_format)
        risk_sheet.write(row, 5, item["label"], formats["text"])
        risk_sheet.write(row, 6, item["description"], formats["text"])
        risk_sheet.write(row, 7, item["evidence_refs"], formats["text"])
        row += 1

    topic_sheet = workbook.add_worksheet("03_topic_rollup")
    topic_sheet.hide_gridlines(2)
    topic_sheet.freeze_panes(1, 0)
    topic_sheet.set_column("A:A", 18)
    topic_sheet.set_column("B:B", 18)
    topic_sheet.set_column("C:C", 24)
    topic_sheet.set_column("D:D", 18)
    topic_sheet.set_column("E:E", 18)
    topic_sheet.set_column("F:F", 70)
    topic_sheet.set_column("G:G", 60)
    topic_sheet.write_row(0, 0, [
        "task_id",
        "report_period",
        "report_type",
        "topic_key",
        "chapter_count",
        "risk_signal_count",
        "summary",
        "analysis_report",
    ], formats["header"])
    row = 1
    for item in topic_rows:
        topic_sheet.write(row, 0, item["task_id"], formats["text"])
        topic_sheet.write(row, 1, item["report_period_label"], formats["text"])
        topic_sheet.write(row, 2, item["report_type_label"], formats["text"])
        topic_sheet.write(row, 3, item["topic_display"], formats["text"])
        topic_sheet.write(row, 4, item["chapter_count"], formats["integer"])
        topic_sheet.write(row, 5, item["risk_signal_count"], formats["integer"])
        topic_sheet.write(row, 6, item["summary"], formats["text"])
        report_path = next((report["analysis_report"] for report in reading_rows if report["task_id"] == item["task_id"]), "")
        topic_sheet.write(row, 7, report_path, formats["text"])
        row += 1

    evidence_sheet = workbook.add_worksheet("99_evidence_index")
    evidence_sheet.hide_gridlines(2)
    evidence_sheet.freeze_panes(1, 0)
    evidence_sheet.set_column("A:A", 18)
    evidence_sheet.set_column("B:B", 18)
    evidence_sheet.set_column("C:C", 14)
    evidence_sheet.set_column("D:D", 18)
    evidence_sheet.set_column("E:E", 20)
    evidence_sheet.set_column("F:F", 18)
    evidence_sheet.set_column("G:G", 14)
    evidence_sheet.set_column("H:H", 30)
    evidence_sheet.set_column("I:I", 22)
    evidence_sheet.set_column("J:J", 22)
    evidence_sheet.set_column("K:K", 14)
    evidence_sheet.set_column("L:L", 18)
    evidence_sheet.set_column("M:M", 12)
    evidence_sheet.write_row(0, 0, [
        "task_id",
        "issuer",
        "year",
        "report_type",
        "evidence_id",
        "field_path",
        "sheet_name",
        "excerpt",
        "source_document",
        "chapter_title",
        "note_no",
        "line_span",
        "confidence",
    ], formats["header"])
    row = 1
    for item in evidence_rows:
        evidence_sheet.write(row, 0, item["task_id"], formats["text"])
        evidence_sheet.write(row, 1, item["issuer"], formats["text"])
        evidence_sheet.write(row, 2, item["year"], formats["integer"])
        evidence_sheet.write(row, 3, item["report_type_label"], formats["text"])
        evidence_sheet.write(row, 4, item["evidence_id"], formats["text"])
        evidence_sheet.write(row, 5, item["field_path"], formats["text"])
        evidence_sheet.write(row, 6, item["sheet_name"], formats["text"])
        evidence_sheet.write(row, 7, item["excerpt"], formats["text"])
        evidence_sheet.write(row, 8, item["source_document"], formats["text"])
        evidence_sheet.write(row, 9, item["chapter_title"], formats["text"])
        evidence_sheet.write(row, 10, item["note_no"], formats["text"])
        evidence_sheet.write(row, 11, metric_value_to_string(item["line_span"]), formats["text"])
        evidence_sheet.write(row, 12, metric_value_to_string(item["confidence"]), formats["text"])
        row += 1

    if metric_rows and any(row.get("value") not in (None, "") for row in metric_rows):
        metrics_sheet = workbook.add_worksheet("04_metric_long")
        metrics_sheet.hide_gridlines(2)
        metrics_sheet.freeze_panes(1, 0)
        metrics_sheet.set_column("A:A", 18)
        metrics_sheet.set_column("B:B", 18)
        metrics_sheet.set_column("C:C", 14)
        metrics_sheet.set_column("D:D", 14)
        metrics_sheet.set_column("E:E", 14)
        metrics_sheet.set_column("F:F", 26)
        metrics_sheet.set_column("G:G", 28)
        metrics_sheet.set_column("H:H", 18)
        metrics_sheet.set_column("I:I", 24)
        metrics_sheet.set_column("J:J", 14)
        metrics_sheet.set_column("K:K", 14)
        metrics_sheet.set_column("L:L", 18)
        metrics_sheet.set_column("M:M", 18)
        metrics_sheet.write_row(0, 0, [
            "task_id",
            "issuer",
            "year",
            "report_type",
            "report_period",
            "category",
            "metric_code",
            "label",
            "value",
            "unit",
            "risk_level",
            "source_status",
            "evidence_refs",
        ], formats["header"])
        row = 1
        for metric in metric_rows:
            metrics_sheet.write(row, 0, metric["task_id"], formats["text"])
            metrics_sheet.write(row, 1, metric["issuer"], formats["text"])
            metrics_sheet.write(row, 2, metric["year"], formats["integer"])
            metrics_sheet.write(row, 3, metric["report_type_label"], formats["text"])
            metrics_sheet.write(row, 4, metric["report_period_label"], formats["text"])
            metrics_sheet.write(row, 5, metric["category"], formats["text"])
            metrics_sheet.write(row, 6, metric["metric_code"], formats["text"])
            metrics_sheet.write(row, 7, metric["label"], formats["text"])
            value, value_kind = format_metric_cells(metric)
            metrics_sheet.write(row, 8, value, formats["number"] if value_kind == "number" else formats["text"])
            metrics_sheet.write(row, 9, metric["unit"], formats["text"])
            risk_format = formats["risk_high"]
            if str(metric["risk_level"]).lower() == "medium":
                risk_format = formats["risk_medium"]
            elif str(metric["risk_level"]).lower() == "low":
                risk_format = formats["risk_low"]
            metrics_sheet.write(row, 10, metric["risk_level"], risk_format)
            metrics_sheet.write(row, 11, metric["source_status"], formats["text"])
            metrics_sheet.write(row, 12, metric["evidence_refs"], formats["text"])
            row += 1

    workbook.close()


def build_master_outputs(output_dir: Path, discovery: Dict[str, Any], summary: Dict[str, Any]) -> Dict[str, Any]:
    master_dir = output_dir / "master"
    master_dir.mkdir(parents=True, exist_ok=True)
    workbook_path = master_dir / "financial_output.xlsx"
    summary_json_path = master_dir / "master_summary.json"
    reading_ledger_path = master_dir / "postformal_reading_ledger.jsonl"
    build_workbook(workbook_path, summary)
    write_jsonl(reading_ledger_path, summary["reading_digest_rows"])

    payload = {
        "generated_at": now_iso(),
        "output_dir": str(output_dir),
        "report_path": str(master_dir / "analysis_report.md"),
        "workbook_path": str(workbook_path),
        "reading_ledger_path": str(reading_ledger_path),
        "report_written_by_script": False,
        "coverage": discovery["coverage"],
        "missing_report_count": len(discovery["missing_reports"]),
        "discovery": discovery["coverage"],
        "report_count": len(summary["reports"]),
        "success_count": sum(1 for row in summary["reports"] if row["status"] == "success"),
        "failure_count": sum(1 for row in summary["reports"] if row["status"] != "success"),
        "missing_reports": discovery["missing_reports"],
        "top_risk_counter": dict(summary["top_risk_counter"]),
        "top_metric_counter": dict(summary["top_metric_counter"]),
        "reading_digest_rows": summary["reading_digest_rows"],
        "topic_rows": summary["topic_rows"],
        "risk_rows": summary["risk_rows"],
        "reports": summary["reports"],
    }
    write_json(summary_json_path, payload)
    return payload


def main():
    args = parse_args()
    try:
        runtime_config = load_runtime_config(
            config_path=Path(args.runtime_config) if args.runtime_config else None,
            cwd=Path.cwd(),
            require_knowledge_base=True,
            ensure_state_dirs=True,
        )
    except RuntimeConfigError as exc:
        raise SystemExit(str(exc)) from exc

    project_root = runtime_project_root(runtime_config)
    output_dir = resolve_output_dir(runtime_config, args.output_dir)
    ensure_under_project_root(output_dir, project_root, "--output-dir")
    discovery_dir = output_dir / "discovery"
    series_dir = output_dir / "series"
    discovery_dir.mkdir(parents=True, exist_ok=True)
    series_dir.mkdir(parents=True, exist_ok=True)

    discovery_payload: Optional[Dict[str, Any]] = None
    if args.postformalize_only:
        selection_manifest_path = discovery_dir / "selection_manifest.json"
        download_config_path = discovery_dir / "download_config.json"
        task_seed_list_path = discovery_dir / "task_seed_list.json"
        discovery_manifest_path = discovery_dir / "discovery_manifest.json"
        if (
            not selection_manifest_path.exists()
            or not download_config_path.exists()
            or not task_seed_list_path.exists()
            or not discovery_manifest_path.exists()
        ):
            raise SystemExit("postformalize-only 模式需要先存在 discovery 产物")
        discovery_payload = read_json(discovery_manifest_path)
        discovery_payload["selection_manifest"] = read_json(selection_manifest_path)
        discovery_payload["download_config"] = read_json(download_config_path)
        discovery_payload["task_seed_list"] = read_json(task_seed_list_path)
        discovery_payload["candidates"] = discovery_payload["task_seed_list"]["tasks"]
        if not (series_dir / SERIES_RESULTS_NAME).exists():
            raise SystemExit("postformalize-only 模式需要先存在 series_task_results.jsonl")
    elif not args.series_only:
        discovery_payload = discover_vanke_reports(args.year_start, args.year_end)
        selection_manifest = build_selection_manifest(discovery_payload, output_dir)
        download_config = build_download_config(discovery_payload, output_dir)
        task_seed_list = build_task_seed_list(discovery_payload, output_dir)

        write_json(discovery_dir / "selection_manifest.json", selection_manifest)
        write_json(discovery_dir / "download_config.json", download_config)
        write_json(discovery_dir / "task_seed_list.json", task_seed_list)
        write_json(discovery_dir / "discovery_manifest.json", discovery_payload)

        if args.prepare_only:
            print(f"[OK] discovery_dir: {discovery_dir}")
            print(f"[OK] selected_count: {len(discovery_payload['candidates'])}")
            print(f"[OK] missing_count: {len(discovery_payload['missing_reports'])}")
            return
    else:
        selection_manifest_path = discovery_dir / "selection_manifest.json"
        download_config_path = discovery_dir / "download_config.json"
        task_seed_list_path = discovery_dir / "task_seed_list.json"
        discovery_manifest_path = discovery_dir / "discovery_manifest.json"
        if (
            not selection_manifest_path.exists()
            or not download_config_path.exists()
            or not task_seed_list_path.exists()
            or not discovery_manifest_path.exists()
        ):
            raise SystemExit("series-only 模式需要先存在 discovery 产物")
        discovery_payload = read_json(discovery_manifest_path)
        discovery_payload["selection_manifest"] = read_json(selection_manifest_path)
        discovery_payload["download_config"] = read_json(download_config_path)
        discovery_payload["task_seed_list"] = read_json(task_seed_list_path)
        discovery_payload["candidates"] = discovery_payload["task_seed_list"]["tasks"]

    series_log_path = output_dir / "run_report_series.log"
    if args.postformalize_only:
        write_text(series_log_path, "[SKIP] postformalize-only: reuse existing series outputs")
    else:
        series_script = SCRIPT_DIR / "run_report_series.py"
        command = build_run_command(sys.executable, series_script, discovery_dir, series_dir, args)
        completed = subprocess.run(command, cwd=str(REPO_ROOT), stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
        write_text(series_log_path, completed.stdout)
        if completed.returncode != 0:
            raise SystemExit(f"run_report_series 失败，日志已写入 {series_log_path}")

    summary = collect_series_records(series_dir, {
        "task_seed_list": read_json(discovery_dir / "task_seed_list.json"),
        "selection_manifest": read_json(discovery_dir / "selection_manifest.json"),
    })

    master_payload = {
        "report_path": "",
        "workbook_path": "",
    }
    if args.formalize:
        master_payload = build_master_outputs(output_dir, discovery_payload, summary)

    study_manifest = {
        "generated_at": now_iso(),
        "output_dir": str(output_dir),
        "discovery_dir": str(discovery_dir),
        "series_dir": str(series_dir),
        "master_dir": str(output_dir / "master"),
        "series_log_path": str(series_log_path),
        "selection_manifest": str(discovery_dir / "selection_manifest.json"),
        "download_config": str(discovery_dir / "download_config.json"),
        "task_seed_list": str(discovery_dir / "task_seed_list.json"),
        "series_manifest": str(series_dir / SERIES_MANIFEST_NAME),
        "series_results": str(series_dir / SERIES_RESULTS_NAME),
        "master_summary": str(output_dir / "master" / "master_summary.json") if args.formalize else "",
        "reading_ledger": str(output_dir / "master" / "postformal_reading_ledger.jsonl") if args.formalize else "",
        "master_report": master_payload["report_path"],
        "master_workbook": master_payload["workbook_path"],
        "master_report_written_by_script": master_payload.get("report_written_by_script", False) if args.formalize else False,
        "formalize": bool(args.formalize),
        "formalization_required": not bool(args.formalize),
        "report_count": len(summary["reports"]),
        "success_count": sum(1 for row in summary["reports"] if row["status"] == "success"),
        "failure_count": sum(1 for row in summary["reports"] if row["status"] != "success"),
    }
    write_json(output_dir / "study_manifest.json", study_manifest)

    print(f"[OK] output_dir: {output_dir}")
    if args.formalize:
        print(f"[OK] master_report_target: {master_payload['report_path']}")
        print(f"[OK] master_workbook: {master_payload['workbook_path']}")
        print("[OK] master_report_written_by_script: false")
    else:
        print("[OK] formalization_required: true")
        print(f"[OK] series_dir: {series_dir}")
        print("[HINT] review 完成后可用 --series-only --resume-output-dir --formalize 复跑正式化")


if __name__ == "__main__":
    main()
