#!/usr/bin/env python3
"""
BondClaw home panel model.

This module defines the data structure the future desktop UI should render on
the first screen.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class HomePanelModel:
    header: Dict[str, Any]
    release_status: Dict[str, Any]
    quick_actions: List[Dict[str, Any]]
    default_context: Dict[str, Any]
    provider_status: List[Dict[str, Any]]
    prompt_shortcuts: List[Dict[str, Any]]
    prompt_center: Dict[str, Any]
    research_brain: Dict[str, Any]
    lead_capture: Dict[str, Any]
    support_banner: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "release_status": self.release_status,
            "quick_actions": self.quick_actions,
            "default_context": self.default_context,
            "provider_status": self.provider_status,
            "prompt_shortcuts": self.prompt_shortcuts,
            "prompt_center": self.prompt_center,
            "research_brain": self.research_brain,
            "lead_capture": self.lead_capture,
            "support_banner": self.support_banner,
        }


def build_home_panel_model(client: RuntimeClient | None = None) -> HomePanelModel:
    runtime_client = client or build_runtime_client()
    settings = runtime_client.settings_snapshot()
    summary = runtime_client.summary()
    branding = summary.get("branding", {})
    release_version = summary.get("release_version", "")
    release_channel = summary.get("release_channel", "")
    feature_flags = summary.get("feature_flags", {})
    update_repo = summary.get("update_repo", "")
    manifest_url = summary.get("manifest_url", "")
    providers = runtime_client.providers()
    roles = runtime_client.roles()
    default_role_id = settings.get("default_role_id", "macro")
    default_prompt_name = settings.get("default_prompt_name", "daily-brief")
    prompt_center = runtime_client.prompt_center_panel(role=default_role_id, prompt_name=default_prompt_name)
    research_brain = runtime_client.research_brain()
    lead_capture = runtime_client.lead_capture()
    lead_capture_submissions = lead_capture.get("submission_summaries", []) if isinstance(lead_capture, dict) else []
    app_name = branding.get("appName", branding.get("app_name", settings.get("app_name", "BondClaw")))
    team_label = branding.get("teamLabel", branding.get("team_label", settings.get("team_label", "国投固收 张亮/叶青")))
    support_banner_copy = branding.get(
        "supportBannerCopy",
        branding.get("support_banner_copy", "支持国投固收研究团队"),
    )

    return HomePanelModel(
        header={
            "app_name": app_name,
            "team_label": team_label,
            "execution_mode": settings.get("execution_mode", settings.get("shell_mode", "native")),
            "runtime_mode": summary.get("shell", {}).get("mode", "native"),
        },
        release_status={
            "release_version": release_version,
            "release_channel": release_channel,
            "update_repo": update_repo,
            "manifest_url": manifest_url,
            "feature_flags": feature_flags,
        },
        quick_actions=[
            {"action_id": "open-provider-settings", "label": "设置 API Key", "kind": "provider"},
            {"action_id": "open-bondclaw-home", "label": "查看 BondClaw 首页", "kind": "primary"},
            {"action_id": "open-prompt-library", "label": "查看模板中心", "kind": "prompt"},
            {"action_id": "open-research-brain", "label": "查看信息中心", "kind": "research"},
            {"action_id": "open-lead-capture", "label": "查看联系方式状态", "kind": "lead"},
            {"action_id": "open-brand-upgrade", "label": "查看品牌与升级", "kind": "upgrade"},
        ],
        default_context={
            "default_provider_id": settings.get("default_provider_id", "zai"),
            "default_role_id": default_role_id,
            "default_prompt_name": default_prompt_name,
            "lead_capture_enabled": settings.get("lead_capture_enabled", True),
            "support_banner_enabled": settings.get("support_banner_enabled", True),
        },
        provider_status=providers,
        prompt_shortcuts=[
            {
                "role_id": role.get("role"),
                "display_name": role.get("display_name"),
                "default_prompt_name": default_prompt_name if role.get("role") == default_role_id else None,
            }
            for role in roles
        ],
        prompt_center={
            "role_count": prompt_center.get("header", {}).get("role_count", 0),
            "workflow_count": prompt_center.get("header", {}).get("workflow_count", 0),
            "sample_count": prompt_center.get("header", {}).get("sample_count", 0),
            "default_role_id": prompt_center.get("default_context", {}).get("default_role_id", ""),
            "default_prompt_name": prompt_center.get("default_context", {}).get("default_prompt_name", ""),
            "selected_role": prompt_center.get("selected_role", {}),
            "selected_prompt": prompt_center.get("selected_prompt", {}),
            "recommended_actions": prompt_center.get("recommended_actions", []),
            "role_cards": prompt_center.get("role_cards", [])[:4],
        },
        research_brain={
            "source_count": research_brain.get("source_count", summary.get("research_source_count", 0)),
            "case_count": research_brain.get("case_count", summary.get("research_case_count", 0)),
            "default_polling_interval": research_brain.get("default_polling_interval", "15m"),
            "notification_order": research_brain.get("notification_order", []),
            "entry_point": "research-brain/feed-sources.example.json",
            "case_index": "research-brain/case-library/index.json",
            "theme_overview": research_brain.get("theme_overview", [])[:4],
            "source_cards": research_brain.get("source_cards", [])[:3],
            "case_cards": research_brain.get("case_summaries", [])[:3],
            "case_highlights": research_brain.get("case_highlights", [])[:3],
        },
        lead_capture={
            "enabled": settings.get("lead_capture_enabled", True),
            "storage": settings.get("api_key_storage", "local-keychain"),
            "queue_count": lead_capture.get("queue_count", summary.get("lead_capture_queue_count", 0)),
            "delivery_order": lead_capture.get("delivery_order", []),
            "submission_count": len(lead_capture_submissions),
            "pending_count": runtime_client.lead_capture_pending_count(),
            "latest_status": lead_capture_submissions[-1].get("delivery_status") if lead_capture_submissions else "",
        },
        support_banner={
            "enabled": settings.get("support_banner_enabled", True),
            "copy": support_banner_copy,
            "display_mode": "visible_only",
        },
    )
