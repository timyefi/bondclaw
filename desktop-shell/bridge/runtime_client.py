#!/usr/bin/env python3
"""
BondClaw desktop runtime client.

Future desktop shells should use this bridge instead of reaching into the
analysis repo directly.
"""

from __future__ import annotations

import json
import subprocess
import sys
from dataclasses import dataclass
from dataclasses import field
from pathlib import Path
from typing import Any, Dict, List, Optional, Sequence, Union

from .settings_store import DesktopSettings, load_settings
from .lead_capture_store import load_queue as load_local_lead_queue, queue_demo_submission, pending_submissions


ROOT = Path(__file__).resolve().parents[2]
DESKTOP_SHELL_DIR = ROOT / "desktop-shell"
for candidate in [
    DESKTOP_SHELL_DIR,
    DESKTOP_SHELL_DIR / "bridge",
    DESKTOP_SHELL_DIR / "home",
    DESKTOP_SHELL_DIR / "pages",
    DESKTOP_SHELL_DIR / "settings",
    DESKTOP_SHELL_DIR / "prompt_center",
    DESKTOP_SHELL_DIR / "research_brain",
    DESKTOP_SHELL_DIR / "lead_capture",
    DESKTOP_SHELL_DIR / "brand_upgrade",
]:
    if str(candidate) not in sys.path:
        sys.path.insert(0, str(candidate))

RUNTIME_SCRIPT = ROOT / "financialanalysis" / "financial-analyzer" / "scripts" / "bondclaw_runtime.py"

ShellArg = Union[str, Path]


@dataclass(frozen=True)
class RuntimeClient:
    python_executable: str = sys.executable
    settings: DesktopSettings = field(default_factory=load_settings)

    @property
    def shell_mode(self) -> str:
        return str(self.settings.shell_mode or "native")

    def _run(self, *args: str) -> Any:
        completed = subprocess.run(
            [self.python_executable, str(RUNTIME_SCRIPT), *args],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=True,
        )
        output = completed.stdout.strip()
        if not output:
            return None
        return json.loads(output)

    def summary(self) -> Dict[str, Any]:
        return self._run("--summary")

    def catalog(self) -> Dict[str, Any]:
        return self._run("--catalog")

    def validate(self) -> List[str]:
        completed = subprocess.run(
            [self.python_executable, str(RUNTIME_SCRIPT), "--validate"],
            cwd=ROOT,
            text=True,
            capture_output=True,
            check=False,
        )
        if completed.returncode == 0:
            return []
        lines = [line.strip() for line in completed.stdout.splitlines() if line.strip()]
        return lines or [completed.stderr.strip() or "BondClaw runtime validation failed"]

    def providers(self) -> List[Dict[str, Any]]:
        return self._run("--providers")

    def roles(self) -> List[Dict[str, Any]]:
        return self._run("--roles")

    def role_manifest(self, role: str) -> Dict[str, Any]:
        return self._run("--role", role)

    def prompt_pack(self, role: str, prompt: str) -> Dict[str, Any]:
        return self._run("--role", role, "--prompt", prompt)

    def prompt_pack_names(self, role: Optional[str] = None) -> List[str]:
        catalog = self.catalog()
        roles = catalog.get("prompt_library", {}).get("roles", {})
        if role is None:
            names: List[str] = []
            for role_payload in roles.values():
                names.extend(role_payload.get("prompt_names", []))
            return names
        role_payload = roles.get(role, {})
        return list(role_payload.get("prompt_names", []))

    def describe_command(self, command: Sequence[ShellArg]) -> Dict[str, str]:
        parts = [str(part) for part in command]
        return self._run("--command", *parts)

    def settings_snapshot(self) -> Dict[str, Any]:
        return {
            "app_name": self.settings.app_name,
            "team_label": self.settings.team_label,
            "shell_mode": self.settings.shell_mode,
            "execution_mode": self.settings.shell_mode,
            "execution_family": "windows-native",
            "default_provider_id": self.settings.default_provider_id,
            "default_role_id": self.settings.default_role_id,
            "default_prompt_name": self.settings.default_prompt_name,
            "lead_capture_enabled": self.settings.lead_capture_enabled,
            "support_banner_enabled": self.settings.support_banner_enabled,
            "notification_level": self.settings.notification_level,
            "api_key_storage": self.settings.api_key_storage,
        }

    def home_panel(self) -> Dict[str, Any]:
        from home.home_model import build_home_panel_model

        return build_home_panel_model(self).to_dict()

    def prompt_center_panel(self, role: Optional[str] = None, prompt_name: Optional[str] = None) -> Dict[str, Any]:
        from prompt_center.prompt_center_model import build_prompt_center_panel_model

        return build_prompt_center_panel_model(self, role=role, prompt_name=prompt_name).to_dict()

    def page_registry(self) -> List[Dict[str, Any]]:
        from pages.page_registry import build_page_registry

        return build_page_registry()

    def navigation_model(self) -> Dict[str, Any]:
        from pages.page_registry import build_navigation_model

        return build_navigation_model(self)

    def research_brain(self) -> Dict[str, Any]:
        return self.summary().get("research_brain", {})

    def lead_capture(self) -> Dict[str, Any]:
        summary = dict(self.summary().get("lead_capture", {}))
        local_queue = load_local_lead_queue().to_dict()
        submissions = []
        for submission in local_queue.get("submissions", []):
            if not isinstance(submission, dict):
                continue
            receipts = submission.get("sink_receipts", {}) or {}
            submissions.append(
                {
                    "name": submission.get("name", ""),
                    "institution": submission.get("institution", ""),
                    "role": submission.get("role", ""),
                    "delivery_status": submission.get("delivery_status", ""),
                    "submitted_at": submission.get("submitted_at", ""),
                    "sink_count": len(receipts),
                }
            )
        summary.update(
            {
                "local_queue": local_queue,
                "queue_count": local_queue.get("queue_count", 0),
                "submission_count": len(local_queue.get("submissions", [])),
                "pending_count": len(pending_submissions()),
                "submission_summaries": submissions,
            }
        )
        return summary

    def research_brain_cases(self, role: Optional[str] = None, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        args: List[str] = ["--research-cases"]
        if role:
            args.extend(["--research-role", role])
        if topic:
            args.extend(["--research-topic", topic])
        return self._run(*args)

    def research_brain_case_details(self, role: Optional[str] = None, topic: Optional[str] = None) -> List[Dict[str, Any]]:
        return self.research_brain_cases(role=role, topic=topic)

    def research_brain_case_detail(self, case_id: str) -> Dict[str, Any]:
        return self._run("--research-case-id", case_id)

    def research_brain_panel(self, role: Optional[str] = None, topic: Optional[str] = None, case_id: Optional[str] = None) -> Dict[str, Any]:
        from research_brain.research_brain_model import build_research_brain_panel_model

        return build_research_brain_panel_model(self, role=role, topic=topic, case_id=case_id).to_dict()

    def lead_capture_panel(self) -> Dict[str, Any]:
        from lead_capture.lead_capture_model import build_lead_capture_panel_model

        return build_lead_capture_panel_model(self).to_dict()

    def brand_upgrade_panel(self) -> Dict[str, Any]:
        from brand_upgrade.brand_upgrade_model import build_brand_upgrade_panel_model

        return build_brand_upgrade_panel_model(self).to_dict()

    def lead_capture_queue(self) -> Dict[str, Any]:
        return load_local_lead_queue().to_dict()

    def lead_capture_pending_count(self) -> int:
        return len(pending_submissions())

    def lead_capture_queue_demo(self, **kwargs: Any) -> Dict[str, Any]:
        return queue_demo_submission(**kwargs).to_dict()


def build_runtime_client(settings: Optional[DesktopSettings] = None) -> RuntimeClient:
    return RuntimeClient(settings=settings or load_settings())
