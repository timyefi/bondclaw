#!/usr/bin/env python3
"""
BondClaw contact panel model.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Dict, List

from bridge.lead_capture_store import load_queue, pending_submissions
from bridge.runtime_client import RuntimeClient, build_runtime_client


@dataclass(frozen=True)
class LeadCapturePanelModel:
    header: Dict[str, Any]
    required_fields: List[str]
    delivery_order: List[str]
    retry_policy: Dict[str, Any]
    queue_status: Dict[str, Any]
    submission_cards: List[Dict[str, Any]]
    sink_notes: List[Dict[str, Any]]
    recommended_actions: List[Dict[str, Any]]
    notes: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "header": self.header,
            "required_fields": self.required_fields,
            "delivery_order": self.delivery_order,
            "retry_policy": self.retry_policy,
            "queue_status": self.queue_status,
            "submission_cards": self.submission_cards,
            "sink_notes": self.sink_notes,
            "recommended_actions": self.recommended_actions,
            "notes": self.notes,
        }


def build_lead_capture_panel_model(client: RuntimeClient | None = None) -> LeadCapturePanelModel:
    runtime_client = client or build_runtime_client()
    summary = runtime_client.lead_capture()
    manifest = summary.get("manifest", {})
    local_queue = load_queue().to_dict()

    submissions = []
    for submission in local_queue.get("submissions", []):
        if not isinstance(submission, dict):
            continue
        receipts = submission.get("sink_receipts", {}) or {}
        submissions.append(
            {
                "name": submission.get("name", ""),
                "role": submission.get("role", ""),
                "delivery_status": submission.get("delivery_status", ""),
                "submitted_at": submission.get("submitted_at", ""),
                "sink_receipt_count": len(receipts),
                "sink_receipts": receipts,
            }
        )

    return LeadCapturePanelModel(
        header={
            "title": "BondClaw 联系方式",
            "description": "首个核心动作触发后收集联系方式，并本地缓存、并行投递、自动重试",
            "queue_count": local_queue.get("queue_count", 0),
            "delivery_status": [item.get("delivery_status") for item in local_queue.get("submissions", [])],
        },
        required_fields=list(manifest.get("required_fields", [])),
        delivery_order=list(manifest.get("default_delivery_order", [])),
        retry_policy=dict(manifest.get("retry_policy", {})),
    queue_status={
            "queue_count": local_queue.get("queue_count", 0),
            "submission_count": len(local_queue.get("submissions", [])),
            "pending_count": len(pending_submissions()),
            "source": "desktop-shell/state/lead-capture.json",
        },
        submission_cards=submissions,
        sink_notes=[
            {
                "sink": "email",
                "status": "parallel",
                "note": "用于触发自动消息通知或邮箱转发。",
            },
            {
                "sink": "persistent_store",
                "status": "local-or-remote",
                "note": "用于保存可查询的最小记录，不要求重型 CRM。",
            },
            {
                "sink": "archive_link",
                "status": "signed-link",
                "note": "用于安全链接或第三方存储中转。",
            },
        ],
        recommended_actions=[
            {"action_id": "open-lead-form", "label": "填写联系方式表单", "kind": "form"},
            {"action_id": "retry-pending", "label": "重试未完成投递", "kind": "retry"},
            {"action_id": "queue-demo-submission", "label": "新增示例提交", "kind": "queue"},
            {"action_id": "open-queue", "label": "查看本地队列", "kind": "queue"},
        ],
        notes=[
            "联系方式必须在首次核心动作前后自然触发，不做重弹窗。",
            "本地队列优先于网络投递，确保断网可继续工作。",
            "三路投递并行，回执记录保留在本地状态里。",
        ],
    )
