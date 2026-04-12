#!/usr/bin/env python3
"""
BondClaw local contact store.

This keeps the desktop-side queue local to the machine and avoids introducing a
heavy backend for V1.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional
from datetime import datetime, timezone


ROOT = Path(__file__).resolve().parents[2]
STATE_DIR = ROOT / "desktop-shell" / "state"
DEFAULT_LEAD_CAPTURE_PATH = STATE_DIR / "lead-capture.json"
EXAMPLE_LEAD_CAPTURE_PATH = STATE_DIR / "lead-capture.example.json"


@dataclass(frozen=True)
class LeadCaptureQueue:
    schemaVersion: int
    queue_count: int
    submissions: List[Dict[str, Any]]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "schemaVersion": self.schemaVersion,
            "queue_count": self.queue_count,
            "submissions": self.submissions,
        }


def read_json(path: Path) -> Dict[str, Any]:
    with path.open("r", encoding="utf-8") as handle:
        payload = json.load(handle)
    if not isinstance(payload, dict):
        raise ValueError(f"contact JSON must be an object: {path}")
    return payload


def write_json(path: Path, payload: Dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8") as handle:
        json.dump(payload, handle, ensure_ascii=False, indent=2)


def load_queue(path: Optional[Path] = None) -> LeadCaptureQueue:
    queue_path = path or DEFAULT_LEAD_CAPTURE_PATH
    if not queue_path.exists():
        queue_path.parent.mkdir(parents=True, exist_ok=True)
        if EXAMPLE_LEAD_CAPTURE_PATH.exists():
            payload = read_json(EXAMPLE_LEAD_CAPTURE_PATH)
        else:
            payload = {"schemaVersion": 1, "queue_count": 0, "submissions": []}
        write_json(queue_path, payload)
    payload = read_json(queue_path)
    return LeadCaptureQueue(
        schemaVersion=int(payload.get("schemaVersion", 1)),
        queue_count=int(payload.get("queue_count", len(payload.get("submissions", [])))),
        submissions=list(payload.get("submissions", [])),
    )


def save_queue(queue: LeadCaptureQueue, path: Optional[Path] = None) -> Path:
    queue_path = path or DEFAULT_LEAD_CAPTURE_PATH
    write_json(queue_path, queue.to_dict())
    return queue_path


def pending_submissions(path: Optional[Path] = None) -> List[Dict[str, Any]]:
    queue = load_queue(path)
    pending: List[Dict[str, Any]] = []
    for submission in queue.submissions:
        if not isinstance(submission, dict):
            continue
        if submission.get("delivery_status") in {"queued", "partial", "failed"}:
            pending.append(submission)
    return pending


def append_submission(submission: Dict[str, Any], path: Optional[Path] = None) -> LeadCaptureQueue:
    queue_path = path or DEFAULT_LEAD_CAPTURE_PATH
    queue = load_queue(queue_path)
    submissions = list(queue.submissions)
    submission = dict(submission)
    submission.setdefault("submitted_at", datetime.now(timezone.utc).isoformat())
    submission.setdefault("delivery_status", "queued")
    submission.setdefault("sink_receipts", {})
    submissions.append(submission)
    updated = LeadCaptureQueue(
        schemaVersion=queue.schemaVersion,
        queue_count=len(submissions),
        submissions=submissions,
    )
    save_queue(updated, queue_path)
    return updated


def build_demo_submission(
    *,
    name: str = "示例新用户",
    institution: str = "示例机构",
    role: str = "宏观研究员",
    email: str = "demo@example.com",
    phone: str = "13800000000",
    card_image: str = "cards/demo.png",
) -> Dict[str, Any]:
    return {
        "name": name,
        "institution": institution,
        "role": role,
        "email": email,
        "phone": phone,
        "card_image": card_image,
        "consent_version": "2026-04",
        "device_id": "desktop-001",
        "client_version": "1.0.0",
        "submitted_at": datetime.now(timezone.utc).isoformat(),
        "delivery_status": "queued",
        "sink_receipts": {
            "email": {"status": "pending"},
            "persistent_store": {"status": "pending"},
            "archive_link": {"status": "pending"},
        },
    }


def queue_demo_submission(path: Optional[Path] = None, **kwargs: Any) -> LeadCaptureQueue:
    return append_submission(build_demo_submission(**kwargs), path=path)
