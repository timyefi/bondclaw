#!/usr/bin/env python3
"""
BondClaw brand and upgrade panel model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class BrandUpgradePanelModel:
    header: Dict[str, Any]
    brand_overview: Dict[str, Any]
    release_overview: Dict[str, Any]
    support_overview: Dict[str, Any]
    feature_flags: List[Dict[str, Any]]
    update_actions: List[Dict[str, Any]]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "brand_overview": self.brand_overview,
            "release_overview": self.release_overview,
            "support_overview": self.support_overview,
            "feature_flags": self.feature_flags,
            "update_actions": self.update_actions,
            "notes": self.notes,
        }


def build_brand_upgrade_panel_model(client: RuntimeClient | None = None) -> BrandUpgradePanelModel:
    runtime_client = client or build_runtime_client()
    summary = runtime_client.summary()
    settings = runtime_client.settings_snapshot()
    release_manifest = summary.get("release_manifest", {}) if isinstance(summary, dict) else {}
    branding = release_manifest.get("branding", {}) if isinstance(release_manifest, dict) else {}
    distribution = release_manifest.get("distribution", {}) if isinstance(release_manifest, dict) else {}
    feature_flags = release_manifest.get("featureFlags", {}) if isinstance(release_manifest, dict) else {}

    def pick(payload: Dict[str, Any], *keys: str, default: Any = "") -> Any:
        for key in keys:
            if key in payload and payload.get(key) not in (None, ""):
                return payload.get(key)
        return default

    manifest_url = pick(distribution, "manifestUrl", "manifest_url", default="")

    return BrandUpgradePanelModel(
        header={
            "title": "BondClaw 品牌与升级",
            "description": "集中查看品牌配置、版本渠道、在线升级和支持入口",
            "app_name": pick(branding, "appName", "app_name", default=settings.get("app_name", "BondClaw")),
            "team_label": pick(branding, "teamLabel", "team_label", default=settings.get("team_label", "国投固收 张亮/叶青 ")),
        },
        brand_overview={
            "app_name": pick(branding, "appName", "app_name"),
            "product_name": pick(branding, "productName", "product_name"),
            "officialWebsite": pick(branding, "officialWebsite", "official_website"),
            "docsBaseUrl": pick(branding, "docsBaseUrl", "docs_base_url"),
            "supportUrl": pick(branding, "supportUrl", "support_url"),
            "supportRibbonCopy": pick(branding, "supportRibbonCopy", "support_ribbon_copy"),
            "supportBannerCopy": pick(branding, "supportBannerCopy", "support_banner_copy"),
            "attributionPolicy": pick(branding, "attributionPolicy", "attribution_policy"),
        },
        release_overview={
            "release_version": summary.get("release_version", ""),
            "release_channel": summary.get("release_channel", ""),
            "update_repo": summary.get("update_repo", ""),
            "manifest_url": manifest_url,
            "runtime_source": "manifest" if release_manifest else "bundled",
            "runtime_loaded_at": "",
        },
        support_overview={
            "support_banner_enabled": settings.get("support_banner_enabled", True),
            "release_notes_url": pick(branding, "releaseNotesUrl", "release_notes_url"),
            "manifest_url": manifest_url,
            "windows_runtime_note": summary.get("shell", {}).get("windows_runtime_note", "Windows 原生运行"),
        },
        feature_flags=[
            {"name": name, "enabled": bool(enabled)}
            for name, enabled in sorted(feature_flags.items(), key=lambda item: item[0])
        ],
        update_actions=[
            {"action_id": "open-release-notes", "label": "查看更新说明", "kind": "external"},
            {"action_id": "open-docs", "label": "查看文档", "kind": "external"},
            {"action_id": "open-official-website", "label": "访问官网", "kind": "external"},
            {"action_id": "open-support-page", "label": "访问支持页", "kind": "external"},
            {"action_id": "refresh-runtime-state", "label": "刷新运行态", "kind": "runtime"},
        ],
        notes=[
            "品牌配置统一从 release manifest 和 runtime state 读取。",
            "在线升级支持远程 manifest 覆盖，但不要求重型后端。",
            "Windows 终端路径已切换为原生进程执行。",
        ],
    )
