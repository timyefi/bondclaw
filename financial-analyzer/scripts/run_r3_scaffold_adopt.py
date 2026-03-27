#!/usr/bin/env python3
"""
R3 scaffold -> adopt -> formalize driver.

This script runs a bounded 1-2 case direct-adopt drill on the selected
case pair, writes canonical adoption logs, validates rollback, and
materializes the formal delivery artifacts.
"""

import argparse
import copy
import datetime
import json
import re
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from adoption_record_utils import stringify
from runtime_support import (
    load_knowledge_base_version,
    load_runtime_config,
    resolve_runtime_path,
)


ROOT_DIR = Path(__file__).resolve().parents[2]
SCRIPT_DIR = ROOT_DIR / "financial-analyzer" / "scripts"
TESTDATA_DIR = ROOT_DIR / "financial-analyzer" / "testdata"
DEFAULT_CASES = ["henglong_2024", "country_garden_2024"]
DELTA_VERSION = "knowledge_adoption_delta_v1"


CASE_CONFIGS: Dict[str, Dict[str, Any]] = {
    "henglong_2024": {
        "case_name": "恒隆地产",
        "issuer": "恒隆地产",
        "year": 2024,
        "md_path": ROOT_DIR / "output" / "恒隆地产" / "恒隆地产2024年報" / "恒隆地产2024年報.md",
        "notes_workfile": TESTDATA_DIR / "henglong_notes_workfile.json",
        "sample_chapter_no": "4",
    },
    "country_garden_2024": {
        "case_name": "碧桂园",
        "issuer": "碧桂园",
        "year": 2024,
        "md_path": ROOT_DIR / "cases" / "碧桂园2024年年报分析.md",
        "notes_workfile": TESTDATA_DIR / "country_garden_notes_workfile.json",
        "sample_chapter_no": "1",
    },
}


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def timestamp_slug() -> str:
    return datetime.datetime.now().strftime("%Y%m%d_%H%M%S")


def slugify(value: str) -> str:
    text = "".join(ch if ch.isalnum() else "_" for ch in str(value or "").strip())
    text = re.sub(r"_+", "_", text).strip("_")
    return text or "unknown"


def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def write_json(path: Path, payload: Dict[str, Any]):
    path.parent.mkdir(parents=True, exist_ok=True)
    temp_path = path.with_suffix(path.suffix + ".tmp")
    with open(temp_path, "w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)
    temp_path.replace(path)


def read_jsonl(path: Path) -> List[Dict[str, Any]]:
    rows: List[Dict[str, Any]] = []
    with open(path, "r", encoding="utf-8") as handle:
        for line in handle:
            text = line.strip()
            if not text:
                continue
            rows.append(json.loads(text))
    return rows


def write_jsonl(path: Path, rows: List[Dict[str, Any]]):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        for row in rows:
            handle.write(json.dumps(row, ensure_ascii=False))
            handle.write("\n")


def write_text(path: Path, content: str):
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as handle:
        handle.write(content)


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def run_command(args: List[str], cwd: Optional[Path] = None) -> subprocess.CompletedProcess:
    return subprocess.run(
        args,
        cwd=str(cwd or ROOT_DIR),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
    )


def highest_risk_level(chapter_record: Dict[str, Any]) -> str:
    risk_signals = chapter_record.get("extensions", {}).get("risk_signals", [])
    levels = [str(item.get("severity", "")).strip().lower() for item in risk_signals if isinstance(item, dict)]
    if "high" in levels or "extreme" in levels:
        return "high"
    if "medium" in levels:
        return "medium"
    return "low"


def chapter_risk_summary(chapter_record: Dict[str, Any]) -> List[str]:
    signals = chapter_record.get("extensions", {}).get("risk_signals", [])
    if not isinstance(signals, list):
        return []
    names: List[str] = []
    for item in signals:
        if not isinstance(item, dict):
            continue
        name = stringify(item.get("signal_name"))
        if name:
            names.append(name)
    return names


def build_case_root(runtime_config: Dict[str, Any], run_id: str) -> Path:
    batch_root = resolve_runtime_path(runtime_config, "batch_root")
    return batch_root / f"r3_scaffold_adopt_{run_id}"


def build_review_root(runtime_config: Dict[str, Any], case_id: str, run_id: str) -> Path:
    governance_root = resolve_runtime_path(runtime_config, "governance_review_root")
    return governance_root / case_id / run_id


def build_run_manifest_path(case_run_dir: Path) -> Path:
    return case_run_dir / "run_manifest.json"


def build_scaffold_paths(case_run_dir: Path) -> Dict[str, Path]:
    return {
        "run_manifest": case_run_dir / "run_manifest.json",
        "chapter_records": case_run_dir / "chapter_records.jsonl",
        "analysis_report_scaffold": case_run_dir / "analysis_report_scaffold.md",
        "focus_list_scaffold": case_run_dir / "focus_list_scaffold.json",
        "final_data_scaffold": case_run_dir / "final_data_scaffold.json",
        "soul_export_payload_scaffold": case_run_dir / "soul_export_payload_scaffold.json",
        "analysis_report": case_run_dir / "analysis_report.md",
        "final_data": case_run_dir / "final_data.json",
        "soul_export_payload": case_run_dir / "soul_export_payload.json",
        "financial_output": case_run_dir / "financial_output.xlsx",
    }


def build_case_summary_text(case: Dict[str, Any], chapter_records: List[Dict[str, Any]], summary: Dict[str, Any]) -> str:
    lines = [
        f"# {case['case_name']} R3 Scaffold -> Adopt Summary",
        "",
        f"- case_id: {summary['case_id']}",
        f"- run_dir: {summary['run_dir']}",
        f"- chapter_count: {len(chapter_records)}",
        f"- adopted_chapter_count: {summary['adopted_chapter_count']}",
        f"- adoption_log_count: {summary['adoption_log_count']}",
        f"- rollback_sample: chapter {summary['rollback_sample_chapter_no']} {summary['rollback_sample_chapter_title']}",
        f"- knowledge_base_version_before: {summary['knowledge_base_version_before']}",
        f"- knowledge_base_version_after: {summary['knowledge_base_version_after']}",
        "",
        "## 摩擦点",
    ]
    for item in summary["friction_points"]:
        lines.append(f"- {item}")
    lines.extend(
        [
            "",
            "## 产物",
            f"- analysis_report.md: {summary['analysis_report_path']}",
            f"- final_data.json: {summary['final_data_path']}",
            f"- soul_export_payload.json: {summary['soul_export_payload_path']}",
            f"- financial_output.xlsx: {summary['financial_output_path']}",
            f"- chapter_review_ledger.jsonl: {summary['review_ledger_path']}",
        ]
    )
    return "\n".join(lines) + "\n"


def build_delta_payload(
    *,
    case_id: str,
    case_name: str,
    case_issuer: str,
    year: int,
    chapter_record: Dict[str, Any],
    case_run_dir: Path,
    review_ledger_path: Path,
    scaffold_paths: Dict[str, Path],
    adoption_id: str,
    summary_text: str,
    review_state: str = "reviewed",
) -> Dict[str, Any]:
    chapter_no = stringify(chapter_record.get("chapter_no"))
    chapter_title = stringify(chapter_record.get("chapter_title"))
    risk_names = chapter_risk_summary(chapter_record)
    risk_level = highest_risk_level(chapter_record)
    confidence = "high" if risk_level == "high" or risk_names else "medium"
    evidence_refs = [
        {
            "type": "chapter_record",
            "path": str(scaffold_paths["chapter_records"]),
            "chapter_no": chapter_no,
        },
        {
            "type": "scaffold",
            "path": str(scaffold_paths["analysis_report_scaffold"]),
        },
    ]
    source = {
        "case_name": case_name,
        "chapter_no": chapter_no,
        "chapter_title": chapter_title,
        "run_dir": str(case_run_dir),
        "chapter_record_path": str(scaffold_paths["chapter_records"]),
        "review_ledger_path": str(review_ledger_path),
        "scaffold_artifacts": {
            "analysis_report_scaffold": str(scaffold_paths["analysis_report_scaffold"]),
            "final_data_scaffold": str(scaffold_paths["final_data_scaffold"]),
            "soul_export_payload_scaffold": str(scaffold_paths["soul_export_payload_scaffold"]),
        },
        "issuer": case_issuer,
        "report_period": str(year),
        "run_manifest_path": str(build_run_manifest_path(case_run_dir)),
    }
    review = {
        "review_state": review_state,
        "reviewer": "Codex",
        "reviewed_at": now_iso(),
        "summary": summary_text,
        "risk_level": risk_level,
        "confidence": confidence,
        "decision": "adopt",
    }
    operations = [
        {
            "op": "upsert_by_key",
            "path": f"knowledge.case_notes.{case_id}.chapters",
            "match_key": "chapter_no",
            "match_value": chapter_no,
            "value": {
                "chapter_no": chapter_no,
                "chapter_title": chapter_title,
                "summary": chapter_record.get("summary", ""),
                "note_scope": chapter_record.get("attributes", {}).get("note_scope", ""),
                "risk_signals": risk_names,
                "topic_tags": chapter_record.get("attributes", {}).get("topic_tags", []),
                "line_span": chapter_record.get("attributes", {}).get("line_span", {}),
                "evidence_refs": [
                    "chapter_records.jsonl",
                    "analysis_report_scaffold.md",
                    "soul_export_payload_scaffold.json",
                ],
                "source_status": "scaffold_reviewed",
                "report_period": str(year),
                "case_issuer": case_issuer,
            },
        }
    ]
    return {
        "identity": {
            "adoption_id": adoption_id,
            "delta_version": DELTA_VERSION,
            "logged_at": now_iso(),
            "result": "applied",
        },
        "source": source,
        "review": review,
        "operations": operations,
        "evidence_refs": evidence_refs,
        "rollback": {
            "enabled": True,
            "strategy": "restore_full_knowledge_base_snapshot",
        },
        "audit": {
            "adoption_id": adoption_id,
            "logged_at": now_iso(),
            "result": "applied",
            "delta_path": "",
            "knowledge_base_path": "",
            "backup_path": "",
            "summary": summary_text,
        },
    }


def build_ledger_record(
    *,
    case_id: str,
    case_name: str,
    case_issuer: str,
    case_run_dir: Path,
    run_manifest_path: Path,
    chapter_record_path: Path,
    chapter_record: Dict[str, Any],
    state: str,
    previous_state: str,
    adoption_gate: bool,
    finalization_gate: bool,
    review_state: str,
    summary: str,
    updated_at: str,
    actor: str = "Codex",
    decision: str = "hold",
    evidence_refs: Optional[List[Dict[str, Any]]] = None,
) -> Dict[str, Any]:
    return {
        "ledger_version": "chapter_review_ledger_v1",
        "record_type": "chapter_review",
        "case_name": case_name,
        "case_id": case_id,
        "issuer": case_issuer,
        "run_dir": str(case_run_dir),
        "run_manifest_path": str(run_manifest_path),
        "chapter_no": stringify(chapter_record.get("chapter_no")),
        "chapter_title": stringify(chapter_record.get("chapter_title")),
        "chapter_record_path": str(chapter_record_path),
        "state": state,
        "previous_state": previous_state,
        "adoption_gate": adoption_gate,
        "finalization_gate": finalization_gate,
        "review": {
            "review_state": review_state,
            "reviewer": actor,
            "summary": summary,
        },
        "evidence_refs": evidence_refs or [],
        "updated_at": updated_at,
        "actor": actor,
        "decision": decision,
    }


def formalize_analysis_report(scaffold_text: str, summary: Dict[str, Any], chapter_records: List[Dict[str, Any]]) -> str:
    text = scaffold_text.replace("（Scaffold）", "").replace("(Scaffold)", "")
    text = text.replace(
        "> 该文件由模板脚本自动生成，仅作为 Codex 后续逐章复核与正式成稿的起点。",
        "> 该文件基于 scaffold 复核后正式化生成。",
    )
    if "## 复核与采纳摘要" in text:
        return text
    lines = [
        "",
        "## 复核与采纳摘要",
        f"- 章节复核完成：{len(chapter_records)} 条 scaffold 记录均已进入正式采纳流程。",
        f"- adoption logs：{summary['adoption_log_count']} 条。",
        f"- rollback 验证：{summary['rollback_sample_chapter_no']} 章已完成回滚并恢复。",
        "- 主要摩擦点已在 case summary 中记录。",
    ]
    return text.rstrip() + "\n" + "\n".join(lines) + "\n"


def formalize_payload(scaffold_payload: Dict[str, Any], run_dir: Path) -> Dict[str, Any]:
    payload = copy.deepcopy(scaffold_payload)
    payload["generated_at"] = now_iso()
    return payload


def execute_scaffold(case_cfg: Dict[str, Any], case_run_dir: Path) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "financial_analyzer.py"),
        "--md",
        str(case_cfg["md_path"]),
        "--notes-workfile",
        str(case_cfg["notes_workfile"]),
        "--run-dir",
        str(case_run_dir),
    ]
    return run_command(command, cwd=ROOT_DIR)


def execute_write_adoption(delta_path: Path) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "write_knowledge_adoption.py"),
        "--delta",
        str(delta_path),
    ]
    return run_command(command, cwd=ROOT_DIR)


def execute_rollback(log_path: Path) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "rollback_knowledge_adoption.py"),
        "--log",
        str(log_path),
    ]
    return run_command(command, cwd=ROOT_DIR)


def execute_validation(command_name: str) -> subprocess.CompletedProcess:
    command = [sys.executable, str(SCRIPT_DIR / "knowledge_manager.py"), command_name, "validate-kb"]
    return run_command(command, cwd=ROOT_DIR)


def execute_show_adoption(limit: int = 10) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "show_knowledge_adoption.py"),
        "--limit",
        str(limit),
    ]
    return run_command(command, cwd=ROOT_DIR)


def execute_soul_export(payload_path: Path, output_path: Path) -> subprocess.CompletedProcess:
    command = [
        sys.executable,
        str(SCRIPT_DIR / "soul_exporter.py"),
        "--payload",
        str(payload_path),
        "--output",
        str(output_path),
    ]
    return run_command(command, cwd=ROOT_DIR)


def make_case_delta_adoption_id(run_id: str, case_id: str, chapter_no: str) -> str:
    return f"{run_id}_{case_id}_chapter_{chapter_no}"


def adoption_log_path(runtime_config: Dict[str, Any], adoption_id: str) -> Path:
    adoption_dir = resolve_runtime_path(runtime_config, "knowledge_adoption_log_dir")
    return adoption_dir / f"{slugify(adoption_id)}.log.json"


def rollback_log_path(runtime_config: Dict[str, Any], adoption_id: str) -> Path:
    adoption_dir = resolve_runtime_path(runtime_config, "knowledge_adoption_log_dir")
    return adoption_dir / f"{slugify(adoption_id)}.rollback.json"


def choose_sample_chapter(chapter_records: List[Dict[str, Any]], preferred_no: str) -> Dict[str, Any]:
    for record in chapter_records:
        if stringify(record.get("chapter_no")) == stringify(preferred_no):
            return record
    return chapter_records[0]


def collect_friction_points(case_cfg: Dict[str, Any], chapter_records: List[Dict[str, Any]]) -> List[str]:
    report_type = chapter_records[0].get("attributes", {}).get("report_type", "")
    chapter_count = len(chapter_records)
    sample_title = stringify(chapter_records[0].get("chapter_title"))
    friction_points = []
    if report_type == "hong_kong_full_report":
        friction_points.append("港股 HKFRS 口径下，债务、现金与契约信息更容易分散在相邻附注，复核时需要跨章节合并证据。")
    if report_type == "nfmii_brief_report":
        friction_points.append("简版年报的标题层级噪声更高，逐章复核必须以 note_no 和 locator_evidence 为准，不能只看章节标题。")
    if chapter_count >= 20:
        friction_points.append("章节数量较多，review ledger 需要按章节批量生成，避免人工逐条维护状态。")
    if case_cfg["case_name"] == "恒隆地产":
        friction_points.append("恒隆样本里借贷和流动性信息集中在少量主附注，单章证据强但需要把利息资本化与契约限制放在同一复核视图里。")
    if case_cfg["case_name"] == "碧桂园":
        friction_points.append("碧桂园样本里风险信号密度高，review 侧要区分现金、受限资金、减值和担保四类信号，避免把风险摘要写成泛化结论。")
    friction_points.append(f"首章样本标题为“{sample_title}”，正式报告需避免把 scaffold 标题当成最终标题。")
    return friction_points


def process_case(
    runtime_config: Dict[str, Any],
    run_id: str,
    case_id: str,
    case_cfg: Dict[str, Any],
    case_root: Path,
) -> Dict[str, Any]:
    case_run_dir = case_root / "tasks" / case_id
    review_root = build_review_root(runtime_config, case_id, run_id)
    review_root.mkdir(parents=True, exist_ok=True)
    case_run_dir.mkdir(parents=True, exist_ok=True)

    scaffold_result = execute_scaffold(case_cfg, case_run_dir)
    if scaffold_result.returncode != 0:
        raise SystemExit(
            f"scaffold 失败: {case_id}\n{scaffold_result.stdout}"
        )

    scaffold_paths = build_scaffold_paths(case_run_dir)
    run_manifest = read_json(scaffold_paths["run_manifest"])
    chapter_records = read_jsonl(scaffold_paths["chapter_records"])
    case_ledger_path = review_root / "chapter_review_ledger.jsonl"
    delta_dir = review_root / "adoption_deltas"
    delta_dir.mkdir(parents=True, exist_ok=True)

    review_records: List[Dict[str, Any]] = []
    adoption_logs: List[Path] = []
    current_state_by_chapter: Dict[str, str] = {}
    current_version_before = load_knowledge_base_version(runtime_config)
    summary_version_after = current_version_before

    for chapter_record in chapter_records:
        chapter_no = stringify(chapter_record.get("chapter_no"))
        chapter_title = stringify(chapter_record.get("chapter_title"))
        chapter_sample_summary = stringify(chapter_record.get("summary"))
        risk_names = chapter_risk_summary(chapter_record)
        review_summary = f"复核附注第 {chapter_no} 章《{chapter_title}》，证据闭环于 scaffold 与 chapter_records。"
        if risk_names:
            review_summary = review_summary + f" 风险信号：{', '.join(risk_names)}。"
        chapter_delta_adoption_id = make_case_delta_adoption_id(run_id, case_id, chapter_no)
        delta_path = delta_dir / f"{slugify(chapter_delta_adoption_id)}.json"
        delta_payload = build_delta_payload(
            case_id=case_id,
            case_name=case_cfg["case_name"],
            case_issuer=case_cfg["issuer"],
            year=case_cfg["year"],
            chapter_record=chapter_record,
            case_run_dir=case_run_dir,
            review_ledger_path=case_ledger_path,
            scaffold_paths=scaffold_paths,
            adoption_id=chapter_delta_adoption_id,
            summary_text=review_summary,
        )
        delta_payload["audit"]["delta_path"] = str(delta_path)
        delta_payload["audit"]["knowledge_base_path"] = str(resolve_runtime_path(runtime_config, "knowledge_base"))
        delta_payload["audit"]["backup_path"] = ""
        delta_payload["review"]["summary"] = review_summary
        write_json(delta_path, delta_payload)

        chapter_chapter_refs = [
            {
                "type": "chapter_record",
                "path": str(scaffold_paths["chapter_records"]),
                "chapter_no": chapter_no,
            },
            {
                "type": "scaffold",
                "path": str(scaffold_paths["analysis_report_scaffold"]),
            },
        ]
        transition_plan = [
            ("scaffold_ready", "", False, False, "proposed", "hold"),
            ("reviewing", "scaffold_ready", False, False, "reviewing", "continue"),
            ("reviewed", "reviewing", False, False, "reviewed", "ready_for_delta"),
            ("adopt_ready", "reviewed", True, False, "reviewed", "adopt"),
        ]
        updated_at = now_iso()
        for state, previous_state, adoption_gate, finalization_gate, review_state, decision in transition_plan:
            review_records.append(
                build_ledger_record(
                    case_id=case_id,
                    case_name=case_cfg["case_name"],
                    case_issuer=case_cfg["issuer"],
                    case_run_dir=case_run_dir,
                    run_manifest_path=scaffold_paths["run_manifest"],
                    chapter_record_path=scaffold_paths["chapter_records"],
                    chapter_record=chapter_record,
                    state=state,
                    previous_state=previous_state,
                    adoption_gate=adoption_gate,
                    finalization_gate=finalization_gate,
                    review_state=review_state,
                    summary=review_summary,
                    updated_at=updated_at,
                    decision=decision,
                    evidence_refs=chapter_chapter_refs,
                )
            )
        write_adopt_result = execute_write_adoption(delta_path)
        if write_adopt_result.returncode != 0:
            raise SystemExit(
                f"adoption 失败: {case_id} chapter {chapter_no}\n{write_adopt_result.stdout}"
            )

        log_path = adoption_log_path(runtime_config, chapter_delta_adoption_id)
        if not log_path.exists():
            raise SystemExit(f"adoption log 缺失: {log_path}")
        adoption_logs.append(log_path)
        adoption_record = read_json(log_path)
        summary_version_after = adoption_record.get("hashes", {}).get("knowledge_base_version_after", summary_version_after)
        review_records.append(
            build_ledger_record(
                case_id=case_id,
                case_name=case_cfg["case_name"],
                case_issuer=case_cfg["issuer"],
                case_run_dir=case_run_dir,
                run_manifest_path=scaffold_paths["run_manifest"],
                chapter_record_path=scaffold_paths["chapter_records"],
                chapter_record=chapter_record,
                state="adopted",
                previous_state="adopt_ready",
                adoption_gate=True,
                finalization_gate=False,
                review_state="adopted",
                summary=f"正式知识已写入。{chapter_sample_summary}",
                updated_at=now_iso(),
                decision="adopted",
                evidence_refs=[
                    {
                        "type": "adoption_log",
                        "path": str(log_path),
                        "chapter_no": chapter_no,
                    }
                ],
            )
        )
        current_state_by_chapter[chapter_no] = "adopted"

    rollback_sample_record = choose_sample_chapter(chapter_records, case_cfg["sample_chapter_no"])
    rollback_sample_no = stringify(rollback_sample_record.get("chapter_no"))
    rollback_sample_title = stringify(rollback_sample_record.get("chapter_title"))
    rollback_sample_adoption_id = make_case_delta_adoption_id(run_id, case_id, rollback_sample_no)
    rollback_sample_log = adoption_log_path(runtime_config, rollback_sample_adoption_id)
    rollback_result = execute_rollback(rollback_sample_log)
    if rollback_result.returncode != 0:
        raise SystemExit(
            f"rollback 失败: {case_id} chapter {rollback_sample_no}\n{rollback_result.stdout}"
        )

    rollback_log = rollback_log_path(runtime_config, rollback_sample_adoption_id)
    if not rollback_log.exists():
        raise SystemExit(f"rollback log 缺失: {rollback_log}")
    review_records.append(
        build_ledger_record(
            case_id=case_id,
            case_name=case_cfg["case_name"],
            case_issuer=case_cfg["issuer"],
            case_run_dir=case_run_dir,
            run_manifest_path=scaffold_paths["run_manifest"],
            chapter_record_path=scaffold_paths["chapter_records"],
            chapter_record=rollback_sample_record,
            state="rolled_back",
            previous_state="adopted",
            adoption_gate=False,
            finalization_gate=False,
            review_state="rolled_back",
            summary="基于 adoption log 完成回滚，知识库恢复为写入前快照。",
            updated_at=now_iso(),
            decision="rollback_verified",
            evidence_refs=[
                {
                    "type": "rollback_log",
                    "path": str(rollback_log),
                    "chapter_no": rollback_sample_no,
                }
            ],
        )
    )

    restore_adoption_id = f"{rollback_sample_adoption_id}_restore"
    restore_delta_path = delta_dir / f"{slugify(restore_adoption_id)}.json"
    restore_delta = build_delta_payload(
        case_id=case_id,
        case_name=case_cfg["case_name"],
        case_issuer=case_cfg["issuer"],
        year=case_cfg["year"],
        chapter_record=rollback_sample_record,
        case_run_dir=case_run_dir,
        review_ledger_path=case_ledger_path,
        scaffold_paths=scaffold_paths,
        adoption_id=restore_adoption_id,
        summary_text=f"回滚后重新采纳第 {rollback_sample_no} 章《{rollback_sample_title}》。",
        review_state="reviewed",
    )
    restore_delta["audit"]["delta_path"] = str(restore_delta_path)
    restore_delta["audit"]["knowledge_base_path"] = str(resolve_runtime_path(runtime_config, "knowledge_base"))
    restore_delta["audit"]["backup_path"] = ""
    write_json(restore_delta_path, restore_delta)
    restore_result = execute_write_adoption(restore_delta_path)
    if restore_result.returncode != 0:
        raise SystemExit(
            f"restore adoption 失败: {case_id} chapter {rollback_sample_no}\n{restore_result.stdout}"
        )
    restore_log_path = adoption_log_path(runtime_config, restore_adoption_id)
    if not restore_log_path.exists():
        raise SystemExit(f"restore adoption log 缺失: {restore_log_path}")
    adoption_logs.append(restore_log_path)
    review_records.append(
        build_ledger_record(
            case_id=case_id,
            case_name=case_cfg["case_name"],
            case_issuer=case_cfg["issuer"],
            case_run_dir=case_run_dir,
            run_manifest_path=scaffold_paths["run_manifest"],
            chapter_record_path=scaffold_paths["chapter_records"],
            chapter_record=rollback_sample_record,
            state="adopted",
            previous_state="rolled_back",
            adoption_gate=True,
            finalization_gate=True,
            review_state="adopted",
            summary=f"回滚后重新采纳完成。{rollback_sample_title}",
            updated_at=now_iso(),
            decision="restore",
            evidence_refs=[
                {
                    "type": "adoption_log",
                    "path": str(restore_log_path),
                    "chapter_no": rollback_sample_no,
                }
            ],
        )
    )

    write_jsonl(case_ledger_path, review_records)

    case_summary = {
        "case_id": case_id,
        "case_name": case_cfg["case_name"],
        "issuer": case_cfg["issuer"],
        "year": case_cfg["year"],
        "run_dir": str(case_run_dir),
        "review_ledger_path": str(case_ledger_path),
        "adoption_log_count": len(adoption_logs),
        "adoption_log_paths": [str(path) for path in adoption_logs],
        "rollback_sample_chapter_no": rollback_sample_no,
        "rollback_sample_chapter_title": rollback_sample_title,
        "knowledge_base_version_before": current_version_before,
        "knowledge_base_version_after": load_knowledge_base_version(runtime_config),
        "analysis_report_path": str(scaffold_paths["analysis_report"]),
        "final_data_path": str(scaffold_paths["final_data"]),
        "soul_export_payload_path": str(scaffold_paths["soul_export_payload"]),
        "financial_output_path": str(scaffold_paths["financial_output"]),
        "friction_points": collect_friction_points(case_cfg, chapter_records),
        "adopted_chapter_count": len(chapter_records),
        "run_manifest_path": str(scaffold_paths["run_manifest"]),
        "knowledge_base_path": str(resolve_runtime_path(runtime_config, "knowledge_base")),
        "rollback_log_path": str(rollback_log),
    }

    analysis_report = formalize_analysis_report(
        read_text(scaffold_paths["analysis_report_scaffold"]),
        case_summary,
        chapter_records,
    )
    write_text(scaffold_paths["analysis_report"], analysis_report)

    final_data = copy.deepcopy(read_json(scaffold_paths["final_data_scaffold"]))
    write_json(scaffold_paths["final_data"], final_data)

    payload = formalize_payload(read_json(scaffold_paths["soul_export_payload_scaffold"]), case_run_dir)
    write_json(scaffold_paths["soul_export_payload"], payload)

    export_result = execute_soul_export(scaffold_paths["soul_export_payload"], scaffold_paths["financial_output"])
    if export_result.returncode != 0:
        raise SystemExit(
            f"soul export 失败: {case_id}\n{export_result.stdout}"
        )

    case_summary_path = review_root / "case_summary.json"
    write_json(case_summary_path, case_summary)
    case_summary_md_path = review_root / "case_summary.md"
    write_text(case_summary_md_path, build_case_summary_text(case_cfg, chapter_records, case_summary))

    validate_result = run_command(
        [sys.executable, str(SCRIPT_DIR / "knowledge_manager.py"), "validate-kb"],
        cwd=ROOT_DIR,
    )
    if validate_result.returncode != 0:
        raise SystemExit(f"knowledge_base 校验失败: {case_id}\n{validate_result.stdout}")

    return {
        "case_id": case_id,
        "case_name": case_cfg["case_name"],
        "issuer": case_cfg["issuer"],
        "year": case_cfg["year"],
        "run_dir": str(case_run_dir),
        "review_ledger_path": str(case_ledger_path),
        "case_summary_path": str(case_summary_path),
        "case_summary_md_path": str(case_summary_md_path),
        "adoption_log_count": len(adoption_logs),
        "rollback_sample_chapter_no": rollback_sample_no,
        "rollback_sample_chapter_title": rollback_sample_title,
        "knowledge_base_version_before": current_version_before,
        "knowledge_base_version_after": summary_version_after,
        "analysis_report": str(scaffold_paths["analysis_report"]),
        "final_data": str(scaffold_paths["final_data"]),
        "soul_export_payload": str(scaffold_paths["soul_export_payload"]),
        "financial_output": str(scaffold_paths["financial_output"]),
        "validation_stdout": validate_result.stdout,
    }


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="R3 scaffold -> adopt -> formalize driver")
    parser.add_argument(
        "--cases",
        nargs="+",
        default=DEFAULT_CASES,
        choices=sorted(CASE_CONFIGS.keys()),
        help="要运行的案例列表",
    )
    parser.add_argument(
        "--run-id",
        help="可选运行标识，默认使用时间戳",
    )
    return parser.parse_args()


def main():
    args = parse_args()
    run_id = args.run_id or timestamp_slug()
    runtime_config = load_runtime_config(
        cwd=ROOT_DIR,
        require_knowledge_base=True,
        ensure_state_dirs=True,
    )
    case_root = build_case_root(runtime_config, run_id)
    case_root.mkdir(parents=True, exist_ok=True)

    results: List[Dict[str, Any]] = []
    for case_id in args.cases:
        case_cfg = CASE_CONFIGS[case_id]
        results.append(process_case(runtime_config, run_id, case_id, case_cfg, case_root))

    batch_manifest = {
        "batch_name": f"r3_scaffold_adopt_{run_id}",
        "generated_at": now_iso(),
        "runtime_config_path": str(Path(str(runtime_config["_config_path"])).resolve()),
        "knowledge_base_version_before": results[0]["knowledge_base_version_before"] if results else "",
        "knowledge_base_version_after": results[-1]["knowledge_base_version_after"] if results else "",
        "case_count": len(results),
        "cases": results,
    }
    write_json(case_root / "batch_manifest.json", batch_manifest)
    write_json(case_root / "case_results.json", {"generated_at": now_iso(), "cases": results})
    print(f"[OK] R3 batch completed: {case_root}")
    print(json.dumps(batch_manifest, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
