#!/usr/bin/env python3
"""
BondClaw template center panel model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class PromptCenterPanelModel:
    header: Dict[str, Any]
    role_cards: List[Dict[str, Any]]
    default_context: Dict[str, Any]
    selected_role: Dict[str, Any]
    selected_prompt: Dict[str, Any]
    recommended_actions: List[Dict[str, Any]]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "role_cards": self.role_cards,
            "default_context": self.default_context,
            "selected_role": self.selected_role,
            "selected_prompt": self.selected_prompt,
            "recommended_actions": self.recommended_actions,
            "notes": self.notes,
        }


def _prompt_preview(prompt_names: List[str], limit: int = 4) -> List[str]:
    return prompt_names[:limit]


def build_prompt_center_panel_model(
    client: RuntimeClient | None = None,
    *,
    role: Optional[str] = None,
    prompt_name: Optional[str] = None,
) -> PromptCenterPanelModel:
    runtime_client = client or build_runtime_client()
    summary = runtime_client.summary()
    catalog = runtime_client.catalog()
    settings = runtime_client.settings_snapshot()
    role_summaries = runtime_client.roles()
    role_catalog = catalog.get("prompt_library", {}).get("roles", {})
    prompt_summaries = summary.get("prompt_pack_summaries", [])

    selected_role_id = role or settings.get("default_role_id", "macro")
    selected_role_manifest = dict(role_catalog.get(selected_role_id, {}))
    selected_role_prompt_names = list(selected_role_manifest.get("prompt_names", []))
    selected_role_summary = next(
        (item for item in prompt_summaries if item.get("role") == selected_role_id),
        {},
    )
    selected_prompt_name = prompt_name
    if not selected_prompt_name and settings.get("default_prompt_name") in selected_role_prompt_names:
        selected_prompt_name = str(settings.get("default_prompt_name", ""))
    if not selected_prompt_name and selected_role_prompt_names:
        selected_prompt_name = selected_role_prompt_names[0]

    selected_prompt_pack: Dict[str, Any] = {}
    selected_prompt_error = ""
    if selected_role_id and selected_prompt_name:
        try:
            selected_prompt_pack = runtime_client.prompt_pack(selected_role_id, selected_prompt_name)
        except Exception as exc:  # pragma: no cover - defensive bridge
            selected_prompt_error = str(exc)

    role_cards: List[Dict[str, Any]] = []
    for role_summary in role_summaries:
        role_id = str(role_summary.get("role", ""))
        manifest = dict(role_catalog.get(role_id, {}))
        prompt_names = list(manifest.get("prompt_names", []))
        role_cards.append(
            {
                "role_id": role_id,
                "display_name": role_summary.get("display_name", role_id),
                "canonical_skill": role_summary.get("canonical_skill", manifest.get("manifest", {}).get("canonical_skill", "")),
                "workflow_count": role_summary.get("workflow_count", len(manifest.get("manifest", {}).get("workflows", []))),
                "sample_count": role_summary.get("sample_count", len(prompt_names)),
                "prompt_preview": _prompt_preview(prompt_names),
                "prompt_count": len(prompt_names),
                "selected": role_id == selected_role_id,
            }
        )

    return PromptCenterPanelModel(
        header={
            "title": "BondClaw 模板中心",
            "description": "按角色浏览模板、样例和 QA 卡，默认直达可用工作流",
            "role_count": len(role_cards),
            "workflow_count": sum(int(card.get("workflow_count", 0)) for card in role_cards),
            "sample_count": sum(int(card.get("sample_count", 0)) for card in role_cards),
            "target_workflow_count_per_role": 20,
        },
        role_cards=role_cards,
        default_context={
            "default_role_id": settings.get("default_role_id", "macro"),
            "default_prompt_name": settings.get("default_prompt_name", "daily-brief"),
            "default_provider_id": settings.get("default_provider_id", "zai"),
            "selected_role_id": selected_role_id,
            "selected_prompt_name": selected_prompt_name,
        },
        selected_role={
            "role_id": selected_role_id,
            "display_name": selected_role_summary.get("display_name", selected_role_id),
            "manifest": selected_role_manifest,
            "prompt_names": selected_role_prompt_names,
            "workflow_count": selected_role_summary.get("workflow_count", len(selected_role_manifest.get("workflows", []))),
            "sample_count": selected_role_summary.get("sample_count", len(selected_role_prompt_names)),
        },
        selected_prompt={
            "prompt_name": selected_prompt_name,
            "prompt_pack": selected_prompt_pack,
            "prompt_error": selected_prompt_error,
        },
        recommended_actions=[
            {"action_id": "open-selected-prompt", "label": "查看选中模板", "kind": "prompt"},
            {"action_id": "browse-by-role", "label": "按角色浏览模板", "kind": "prompt-browser"},
            {"action_id": "open-role-manifest", "label": "查看角色清单", "kind": "manifest"},
            {"action_id": "open-template-library", "label": "查看当前模板", "kind": "prompt"},
            {"action_id": "open-expansion-plan", "label": "查看扩展计划", "kind": "plan"},
        ],
        notes=[
            "模板中心保持本地目录优先读取。",
            "每个角色先看 manifest，再看具体模板卡。",
            "后续可把 selected_prompt 直接作为执行入口。",
        ],
    )
