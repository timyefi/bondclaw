#!/usr/bin/env python3
"""Build the BondClaw prompt expansion plan from role manifests."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List


ROOT = Path(__file__).resolve().parent
PACKS_DIR = ROOT / "packs"
TARGET_WORKFLOW_COUNT = 20
TARGET_VARIANT_COUNT = 5


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"JSON 顶层必须是对象: {path}")
    return payload


def build_role_plan(role_dir: Path) -> Dict[str, Any]:
    manifest = read_json(role_dir / "manifest.json")
    workflows = list(manifest.get("workflows") or [])
    placeholders = []
    for index in range(len(workflows) + 1, TARGET_WORKFLOW_COUNT + 1):
        placeholders.append(f"workflow_{index:02d}")
    return {
        "role": manifest.get("role", role_dir.name),
        "display_name": manifest.get("display_name", role_dir.name),
        "canonical_skill": manifest.get("canonical_skill", "research-writing"),
        "target_workflow_count": TARGET_WORKFLOW_COUNT,
        "target_variant_count": TARGET_VARIANT_COUNT,
        "existing_workflows": workflows,
        "placeholder_workflows": placeholders,
        "sample_pack_count": len([path for path in role_dir.glob("*.json") if path.name != "manifest.json"]),
    }


def build_plan() -> Dict[str, Any]:
    roles = []
    if PACKS_DIR.exists():
        for role_dir in sorted(path for path in PACKS_DIR.iterdir() if path.is_dir()):
            if (role_dir / "manifest.json").exists():
                roles.append(build_role_plan(role_dir))
    return {
        "target_workflow_count": TARGET_WORKFLOW_COUNT,
        "target_variant_count": TARGET_VARIANT_COUNT,
        "role_count": len(roles),
        "roles": roles,
    }


def main() -> int:
    print(json.dumps(build_plan(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
