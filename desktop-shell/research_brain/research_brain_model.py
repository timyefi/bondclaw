#!/usr/bin/env python3
"""
BondClaw 信息中心面板模型。

This module turns the subscription manifest and case library into a first-class
panel the desktop shell can render.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List, Optional

from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class ResearchBrainPanelModel:
    header: Dict[str, Any]
    source_groups: List[Dict[str, Any]]
    source_cards: List[Dict[str, Any]]
    theme_overview: List[Dict[str, Any]]
    filters: Dict[str, Any]
    case_browser: Dict[str, Any]
    case_details: Dict[str, Any]
    case_highlights: List[Dict[str, Any]]
    prompt_shortcuts: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "source_groups": self.source_groups,
            "source_cards": self.source_cards,
            "theme_overview": self.theme_overview,
            "filters": self.filters,
            "case_browser": self.case_browser,
            "case_details": self.case_details,
            "case_highlights": self.case_highlights,
            "prompt_shortcuts": self.prompt_shortcuts,
            "recommended_actions": self.recommended_actions,
            "notes": self.notes,
        }


def _role_labels(role_payloads: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    return [
        {
            "role_id": role.get("role"),
            "display_name": role.get("display_name"),
            "workflow_count": role.get("workflow_count", len(role.get("workflows") or [])),
            "sample_pack_count": role.get("sample_count", len(role.get("sample_packs") or [])),
        }
        for role in role_payloads
    ]


def _build_source_cards(source_groups: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    cards: List[Dict[str, Any]] = []
    for group in source_groups:
        topic_tags = list(group.get("topic_tags") or [])
        role_tags = list(group.get("role_tags") or [])
        cards.append(
            {
                "group_id": group.get("group_id", ""),
                "title": group.get("display_name", ""),
                "topic_count": len(topic_tags),
                "role_count": len(role_tags),
                "topic_tags": topic_tags[:4],
                "role_tags": role_tags[:4],
                "polling_interval": group.get("polling_interval", ""),
                "notification_policy": group.get("notification_policy", ""),
                "summary": f"{len(topic_tags)} 个主题标签，覆盖 {len(role_tags)} 个角色标签",
            }
        )
    return cards


def build_research_brain_panel_model(
    client: RuntimeClient | None = None,
    *,
    role: Optional[str] = None,
    topic: Optional[str] = None,
    case_id: Optional[str] = None,
) -> ResearchBrainPanelModel:
    runtime_client = client or build_runtime_client()
    summary = runtime_client.research_brain()
    roles = runtime_client.roles()
    cases = runtime_client.research_brain_cases(role=role, topic=topic)
    case_details = runtime_client.research_brain_case_details(role=role, topic=topic)
    selected_case = runtime_client.research_brain_case_detail(case_id) if case_id else None
    current_role = role or runtime_client.settings_snapshot().get("default_role_id", "macro")
    current_topic = topic or ""
    current_case_id = case_id or ""
    prompt_shortcuts: List[Dict[str, Any]] = []
    if selected_case:
        prompt_pack = selected_case.get("prompt_pack", {}) if isinstance(selected_case, dict) else {}
        prompt_shortcuts.append(
            {
                "prompt_role": selected_case.get("prompt_role"),
                "workflow": selected_case.get("prompt_workflow"),
                "prompt_name": selected_case.get("recommended_prompt"),
                "prompt_title": str(prompt_pack.get("prompt_template", ""))[:48],
                "output_format": prompt_pack.get("output_format"),
                "qa_checklist": prompt_pack.get("qa_checklist", []),
            }
        )
    source_cards = _build_source_cards(summary.get("source_groups", []))
    theme_overview = summary.get("theme_overview", [])
    case_highlights = []
    for item in case_details[:3]:
        case_highlights.append(
            {
                "case_id": item.get("case_id", ""),
                "title": item.get("title", ""),
                "prompt_role": item.get("prompt_role", ""),
                "prompt_workflow": item.get("prompt_workflow", ""),
                "summary": item.get("summary", ""),
                "topic_tags": item.get("topic_tags", []),
                "role_tags": item.get("role_tags", []),
            }
        )

    return ResearchBrainPanelModel(
        header={
            "title": "BondClaw 信息中心",
            "description": "订阅源、案例卡、案例筛选和研究提醒都在这里集中浏览",
            "source_count": summary.get("source_count", 0),
            "case_count": summary.get("case_count", 0),
            "default_polling_interval": summary.get("default_polling_interval", "15m"),
        },
        source_groups=summary.get("source_groups", []),
        source_cards=source_cards,
        theme_overview=theme_overview,
        filters={
            "selected_role": current_role,
            "selected_topic": current_topic,
            "selected_case_id": current_case_id,
            "available_roles": _role_labels(roles),
            "available_topics": sorted(
                {
                    tag
                    for group in summary.get("source_groups", [])
                    for tag in (group.get("topic_tags") or [])
                }
            ),
            "case_count": len(cases),
        },
        case_browser={
            "entry_point": "research-brain/case-library/index.json",
            "notification_order": summary.get("notification_order", []),
            "cases": cases,
            "case_cards": cases[:6],
        },
        case_details={
            "selected_case": selected_case,
            "visible_case_cards": case_details[:6],
            "case_index_path": "research-brain/case-library/index.json",
            "selected_prompt_pack": (selected_case or {}).get("prompt_pack", {}),
            "selected_prompt_error": (selected_case or {}).get("prompt_pack_error", ""),
            "evidence_card": {
                "title": (selected_case or {}).get("title", ""),
                "summary": (selected_case or {}).get("summary", ""),
                "source_refs": (selected_case or {}).get("source_refs", []),
                "evidence_hints": (selected_case or {}).get("evidence_hints", []),
            } if selected_case else {},
            "prompt_card": {
                "title": (selected_case or {}).get("recommended_prompt", ""),
                "workflow": (selected_case or {}).get("prompt_workflow", ""),
                "role": (selected_case or {}).get("prompt_role", ""),
                "prompt_template": ((selected_case or {}).get("prompt_pack", {}) or {}).get("prompt_template", ""),
                "output_format": ((selected_case or {}).get("prompt_pack", {}) or {}).get("output_format", ""),
                "qa_checklist": ((selected_case or {}).get("prompt_pack", {}) or {}).get("qa_checklist", []),
            } if selected_case else {},
            "action_card": {
                "case_id": (selected_case or {}).get("case_id", ""),
                "primary_action": "open-selected-prompt" if selected_case else "",
                "secondary_action": "browse-by-role" if selected_case else "",
                "recommended_prompt": (selected_case or {}).get("recommended_prompt", ""),
            } if selected_case else {},
        },
        case_highlights=case_highlights,
        prompt_shortcuts=prompt_shortcuts,
        recommended_actions=[
            {"action_id": "refresh-feeds", "label": "刷新订阅", "kind": "subscription"},
            {"action_id": "filter-by-theme", "label": "按主题筛选案例", "kind": "theme-filter"},
            {"action_id": "browse-by-role", "label": "按角色浏览案例", "kind": "case-browser"},
            {"action_id": "open-selected-case", "label": "查看选中案例", "kind": "case-detail"},
            {"action_id": "open-selected-prompt", "label": "查看对应 Prompt", "kind": "prompt"},
            {"action_id": "open-highlighted-prompt", "label": "查看高亮 Prompt", "kind": "prompt"},
            {"action_id": "open-case-library", "label": "查看案例库", "kind": "case-library"},
        ],
        notes=[
            "案例卡和订阅源会走本地缓存优先。",
            "筛选只是在面板层收口，不改变底层 manifest。",
            "后续可把 selected_role 直接映射到 Prompt 快捷入口。",
        ],
    )
