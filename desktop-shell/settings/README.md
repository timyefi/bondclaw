# Settings Panel

This directory holds the settings screen model for BondClaw.

## Files

- `settings_model.py`

## Purpose

The settings screen combines execution mode, provider defaults, prompt
defaults, privacy settings, appearance controls, and help text into a single
renderable data model.

The customer-facing label is now "Windows 原生执行" rather than a shell
selection screen.

## Related contract

- `desktop-shell/contracts/desktop-settings.contract.json`
- `desktop-shell/contracts/settings-panel.contract.json`
