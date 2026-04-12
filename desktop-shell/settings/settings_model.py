#!/usr/bin/env python3
"""
BondClaw settings panel model.

This module describes the first-class settings screen for the desktop shell.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class SettingsPanelModel:
    header: Dict[str, Any]
    runtime_settings: Dict[str, Any]
    provider_settings: Dict[str, Any]
    prompt_settings: Dict[str, Any]
    privacy_settings: Dict[str, Any]
    appearance_settings: Dict[str, Any]
    available_providers: List[Dict[str, Any]]
    available_roles: List[Dict[str, Any]]
    available_prompts: List[str]
    help_text: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "runtime_settings": self.runtime_settings,
            "provider_settings": self.provider_settings,
            "prompt_settings": self.prompt_settings,
            "privacy_settings": self.privacy_settings,
            "appearance_settings": self.appearance_settings,
            "available_providers": self.available_providers,
            "available_roles": self.available_roles,
            "available_prompts": self.available_prompts,
            "help_text": self.help_text,
        }


def build_settings_panel_model(client: RuntimeClient | None = None) -> SettingsPanelModel:
    runtime_client = client or build_runtime_client()
    settings = runtime_client.settings_snapshot()
    providers = runtime_client.providers()
    roles = runtime_client.roles()
    current_role = settings.get("default_role_id", "macro")
    current_prompt = settings.get("default_prompt_name", "daily-brief")

    return SettingsPanelModel(
        header={
            "title": "BondClaw 设置",
            "team_label": settings.get("team_label", "国投固收 张亮/叶青"),
            "description": "管理 Windows 原生执行、provider、默认角色、Prompt 和本地行为",
        },
        runtime_settings={
            "execution_mode": settings.get("execution_mode", settings.get("shell_mode", "native")),
            "execution_family": settings.get("execution_family", "windows-native"),
            "notification_level": settings.get("notification_level", "normal"),
        },
        provider_settings={
            "default_provider_id": settings.get("default_provider_id", "zai"),
            "provider_count": len(providers),
            "key_only_flow": True,
        },
        prompt_settings={
            "default_role_id": current_role,
            "default_prompt_name": current_prompt,
            "role_count": len(roles),
        },
        privacy_settings={
            "lead_capture_enabled": settings.get("lead_capture_enabled", True),
            "api_key_storage": settings.get("api_key_storage", "local-keychain"),
        },
        appearance_settings={
            "support_banner_enabled": settings.get("support_banner_enabled", True),
            "support_banner_copy": "研究开发不易，请大力支持国投固收研究 张亮/叶青",
        },
        available_providers=providers,
        available_roles=roles,
        available_prompts=runtime_client.prompt_pack_names(role=current_role),
        help_text=[
            "用户正常情况下只需要填 API Key。",
            "Windows 场景默认走原生进程。",
            "联系方式和支持条属于可见但非打扰式配置。",
            "默认 prompt 会影响首页快捷入口。",
        ],
    )
