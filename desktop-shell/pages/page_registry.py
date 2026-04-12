#!/usr/bin/env python3
"""
BondClaw desktop page registry.

This defines the first-screen and secondary navigation model for the future
desktop shell UI.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class PageDescriptor:
    page_id: str
    title: str
    section: str
    description: str
    source: str

    def to_dict(self) -> Dict[str, str]:
        return {
            "page_id": self.page_id,
            "title": self.title,
            "section": self.section,
            "description": self.description,
            "source": self.source,
        }


PAGE_DESCRIPTORS: List[PageDescriptor] = [
    PageDescriptor("home", "首页", "primary", "查看摘要、快捷入口和当前默认上下文", "runtime summary + settings"),
    PageDescriptor("bondclaw", "BondClaw 首页", "primary", "查看模板中心、信息中心和联系方式的总览", "aionui home dashboard"),
    PageDescriptor("settings", "设置", "primary", "配置执行模式、provider、默认角色和模板", "desktop settings"),
    PageDescriptor("providers", "Provider", "content", "管理 API Key 和 coding plan 预置", "provider registry"),
    PageDescriptor("prompts", "模板中心", "content", "浏览角色模板、样例和 QA 卡", "template center"),
    PageDescriptor("research-brain", "信息中心", "content", "浏览订阅源、案例卡和研究提醒", "research brain"),
    PageDescriptor("lead-capture", "联系方式", "utility", "查看联系方式状态和投递链路", "lead capture"),
    PageDescriptor("brand-upgrade", "品牌与升级", "utility", "查看品牌配置、版本渠道和在线升级状态", "release manifest"),
    PageDescriptor("logs", "运行日志", "utility", "查看 runtime validation 与页面日志", "runtime bridge"),
    PageDescriptor("about", "关于", "utility", "查看品牌、团队和版本信息", "branding + runtime"),
]


def build_page_registry() -> List[Dict[str, str]]:
    return [descriptor.to_dict() for descriptor in PAGE_DESCRIPTORS]


def get_page_descriptor(page_id: str) -> PageDescriptor:
    for descriptor in PAGE_DESCRIPTORS:
        if descriptor.page_id == page_id:
            return descriptor
    raise KeyError(f"Unknown page: {page_id}")


def build_navigation_model(client: RuntimeClient | None = None) -> Dict[str, Any]:
    runtime_client = client or build_runtime_client()
    settings = runtime_client.settings_snapshot()
    provider_id = settings.get("default_provider_id", "zai")
    role_id = settings.get("default_role_id", "macro")
    prompt_name = settings.get("default_prompt_name", "daily-brief")
    return {
        "shell_id": "bondclaw-desktop-shell",
        "default_page_id": "home",
        "active_context": {
            "provider_id": provider_id,
            "role_id": role_id,
            "prompt_name": prompt_name,
        },
        "pages": build_page_registry(),
        "sidebar_sections": {
            "primary": ["home", "bondclaw", "settings"],
            "content": ["providers", "prompts", "research-brain"],
            "utility": ["lead-capture", "brand-upgrade", "logs", "about"],
        },
        "default_navigation": {
            "primary": ["home", "bondclaw", "settings", "providers", "prompts"],
            "secondary": ["research-brain", "lead-capture", "brand-upgrade", "logs", "about"],
        },
    }
