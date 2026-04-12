#!/usr/bin/env python3
"""Minimal BondClaw desktop-shell launcher stub."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
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

from bridge.runtime_client import build_runtime_client
from settings.settings_model import build_settings_panel_model


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Launch the BondClaw desktop shell stub")
    parser.add_argument("--summary", action="store_true", help="Print runtime summary")
    parser.add_argument("--catalog", action="store_true", help="Print runtime catalog")
    parser.add_argument("--providers", action="store_true", help="Print provider matrix")
    parser.add_argument("--roles", action="store_true", help="Print role summaries")
    parser.add_argument("--settings", action="store_true", help="Print desktop settings")
    parser.add_argument("--home", action="store_true", help="Print the home panel model")
    parser.add_argument("--settings-panel", action="store_true", help="Print the settings panel model")
    parser.add_argument("--pages", action="store_true", help="Print the page registry")
    parser.add_argument("--navigation", action="store_true", help="Print the navigation model")
    parser.add_argument("--prompt-center-panel", action="store_true", help="Print the template center panel model")
    parser.add_argument("--prompt-role", help="Select a template center role")
    parser.add_argument("--prompt-name", help="Select a template center prompt")
    parser.add_argument("--research-brain-panel", action="store_true", help="Print the subscriptions and cases panel model")
    parser.add_argument("--research-role", help="Filter subscription and case entries by role")
    parser.add_argument("--research-topic", help="Filter subscription and case entries by topic")
    parser.add_argument("--research-case-id", help="Select a subscription/case entry")
    parser.add_argument("--lead-capture-panel", action="store_true", help="Print the contact panel model")
    parser.add_argument("--lead-capture-pending", action="store_true", help="Print the number of pending contact submissions")
    parser.add_argument("--lead-capture-demo", action="store_true", help="Append a demo contact submission and print the updated queue")
    parser.add_argument("--brand-upgrade-panel", action="store_true", help="Print the brand and upgrade panel model")
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    client = build_runtime_client()
    if args.catalog:
        print(json.dumps(client.catalog(), ensure_ascii=False, indent=2))
        return 0
    if args.providers:
        print(json.dumps(client.providers(), ensure_ascii=False, indent=2))
        return 0
    if args.roles:
        print(json.dumps(client.roles(), ensure_ascii=False, indent=2))
        return 0
    if args.settings:
        print(json.dumps(client.settings_snapshot(), ensure_ascii=False, indent=2))
        return 0
    if args.home:
        print(json.dumps(client.home_panel(), ensure_ascii=False, indent=2))
        return 0
    if args.settings_panel:
        print(json.dumps(build_settings_panel_model(client).to_dict(), ensure_ascii=False, indent=2))
        return 0
    if args.pages:
        print(json.dumps(client.page_registry(), ensure_ascii=False, indent=2))
        return 0
    if args.navigation:
        print(json.dumps(client.navigation_model(), ensure_ascii=False, indent=2))
        return 0
    if args.prompt_center_panel:
        print(json.dumps(client.prompt_center_panel(role=args.prompt_role, prompt_name=args.prompt_name), ensure_ascii=False, indent=2))
        return 0
    if args.research_brain_panel:
        print(json.dumps(client.research_brain_panel(role=args.research_role, topic=args.research_topic, case_id=args.research_case_id), ensure_ascii=False, indent=2))
        return 0
    if args.lead_capture_panel:
        print(json.dumps(client.lead_capture_panel(), ensure_ascii=False, indent=2))
        return 0
    if args.lead_capture_pending:
        print(json.dumps({"pending_count": client.lead_capture_pending_count()}, ensure_ascii=False, indent=2))
        return 0
    if args.lead_capture_demo:
        print(json.dumps(client.lead_capture_queue_demo(), ensure_ascii=False, indent=2))
        return 0
    if args.brand_upgrade_panel:
        print(json.dumps(client.brand_upgrade_panel(), ensure_ascii=False, indent=2))
        return 0
    print(json.dumps(client.summary(), ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
