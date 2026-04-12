#!/usr/bin/env python3
"""
BondClaw local desktop settings store.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Optional


ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "desktop-shell" / "state"
DEFAULT_SETTINGS_PATH = STATE_DIR / "desktop-settings.json"
EXAMPLE_SETTINGS_PATH = STATE_DIR / "desktop-settings.example.json"


@dataclass(frozen=True)
class DesktopSettings:
    app_name: str = "BondClaw"
    team_label: str = "国投固收 张亮/叶青"
    shell_mode: str = "native"
    default_provider_id: str = "zai"
    default_role_id: str = "macro"
    default_prompt_name: str = "daily-brief"
    lead_capture_enabled: bool = True
    support_banner_enabled: bool = True
    notification_level: str = "normal"
    api_key_storage: str = "local-keychain"


def _default_payload() -> Dict[str, Any]:
    return {
        "app_name": "BondClaw",
        "team_label": "国投固收 张亮/叶青",
        "execution_mode": "native",
        "shell_mode": "native",
        "default_provider_id": "zai",
        "default_role_id": "macro",
        "default_prompt_name": "daily-brief",
        "lead_capture_enabled": True,
        "support_banner_enabled": True,
        "notification_level": "normal",
        "api_key_storage": "local-keychain",
    }


def load_settings(path: Optional[Path] = None) -> DesktopSettings:
    settings_path = path or DEFAULT_SETTINGS_PATH
    if not settings_path.exists():
        settings_path.parent.mkdir(parents=True, exist_ok=True)
        if EXAMPLE_SETTINGS_PATH.exists():
            payload = read_json(EXAMPLE_SETTINGS_PATH)
        else:
            payload = _default_payload()
        write_json(settings_path, payload)
    payload = read_json(settings_path)
    return DesktopSettings(
        app_name=str(payload.get("app_name", "BondClaw")),
        team_label=str(payload.get("team_label", "国投固收 张亮/叶青")),
        shell_mode=str(payload.get("execution_mode", payload.get("shell_mode", "native"))),
        default_provider_id=str(payload.get("default_provider_id", "zai")),
        default_role_id=str(payload.get("default_role_id", "macro")),
        default_prompt_name=str(payload.get("default_prompt_name", "daily-brief")),
        lead_capture_enabled=bool(payload.get("lead_capture_enabled", True)),
        support_banner_enabled=bool(payload.get("support_banner_enabled", True)),
        notification_level=str(payload.get("notification_level", "normal")),
        api_key_storage=str(payload.get("api_key_storage", "local-keychain")),
    )


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"settings JSON must be an object: {path}")
    return payload


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def save_settings(settings: DesktopSettings, path: Optional[Path] = None) -> Path:
    settings_path = path or DEFAULT_SETTINGS_PATH
    write_json(
        settings_path,
        {
            "app_name": settings.app_name,
            "team_label": settings.team_label,
            "execution_mode": settings.shell_mode,
            "shell_mode": settings.shell_mode,
            "default_provider_id": settings.default_provider_id,
            "default_role_id": settings.default_role_id,
            "default_prompt_name": settings.default_prompt_name,
            "lead_capture_enabled": settings.lead_capture_enabled,
            "support_banner_enabled": settings.support_banner_enabled,
            "notification_level": settings.notification_level,
            "api_key_storage": settings.api_key_storage,
        },
    )
    return settings_path
