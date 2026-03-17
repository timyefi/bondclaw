#!/usr/bin/env python3
"""
运行时配置与批处理共享元数据辅助模块。
"""

import datetime
import json
from pathlib import Path
from typing import Any, Dict, Optional


ROOT_DIR = Path(__file__).resolve().parents[2]
DEFAULT_RUNTIME_CONFIG_PATH = ROOT_DIR / "runtime" / "runtime_config.json"
LEGACY_BATCH_ROOT = ROOT_DIR / "financial-analyzer" / "test_runs" / "batches"


def now_iso() -> str:
    return datetime.datetime.now().astimezone().isoformat(timespec="seconds")


def read_json(path: Path) -> Dict[str, Any]:
    with open(path, "r", encoding="utf-8") as handle:
        return json.load(handle)


def read_text(path: Path) -> str:
    with open(path, "r", encoding="utf-8") as handle:
        return handle.read()


def try_load_runtime_config(config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    candidate = (config_path or DEFAULT_RUNTIME_CONFIG_PATH).resolve()
    if not candidate.exists():
        return None
    payload = read_json(candidate)
    payload["_config_path"] = str(candidate)
    return payload


def load_runtime_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    payload = try_load_runtime_config(config_path=config_path)
    if payload is None:
        raise FileNotFoundError(f"runtime_config.json 不存在: {(config_path or DEFAULT_RUNTIME_CONFIG_PATH).resolve()}")
    return payload


def runtime_project_root(runtime_config: Dict[str, Any]) -> Path:
    return Path(str(runtime_config["project_root"])).resolve()


def resolve_runtime_path(runtime_config: Dict[str, Any], key: str) -> Path:
    project_root = runtime_project_root(runtime_config)
    relative_path = runtime_config["paths"][key]
    resolved = (project_root / relative_path).resolve()
    if runtime_config.get("policies", {}).get("require_paths_under_project_root", False):
        try:
            resolved.relative_to(project_root)
        except ValueError as exc:
            raise ValueError(f"runtime 路径超出项目根目录: {resolved}") from exc
    return resolved


def resolve_default_batch_root(runtime_config: Optional[Dict[str, Any]]) -> Path:
    if runtime_config is None:
        return LEGACY_BATCH_ROOT
    return resolve_runtime_path(runtime_config, "batch_root")


def load_knowledge_base_version(runtime_config: Optional[Dict[str, Any]]) -> str:
    if runtime_config is None:
        return ""

    knowledge_base_path = resolve_runtime_path(runtime_config, "knowledge_base")
    if not knowledge_base_path.exists():
        return ""

    payload = read_json(knowledge_base_path)
    metadata = payload.get("metadata") or {}
    return str(metadata.get("version", ""))


def current_engine_version() -> str:
    from financial_analyzer import ENGINE_VERSION

    return str(ENGINE_VERSION)


def detect_report_identity(md_path: Path) -> Dict[str, str]:
    from financial_analyzer import (
        classify_report,
        extract_company_name,
        extract_report_period,
        normalize_text,
    )

    raw_text = normalize_text(read_text(md_path))
    company_name = extract_company_name(raw_text, md_path.stem)
    report_period = extract_report_period(raw_text, md_path.stem)
    classification = classify_report(raw_text, md_path)
    return {
        "company_name": company_name,
        "report_period": report_period,
        "report_type": str(classification.get("report_type", "")),
        "audit_opinion": str(classification.get("audit_opinion", "")),
    }


def md5_file(path: Path) -> str:
    from financial_analyzer import md5_file as analyzer_md5_file

    return str(analyzer_md5_file(path))
