# BondClaw Desktop Shell

This directory is the desktop-shell skeleton for BondClaw.

## What lives here

- A stable bridge from the future UI shell to the BondClaw runtime facade.
- Shell-level contracts that stay independent from the analysis core.
- Windows-native execution helpers that keep the customer flow free of extra terminal setup.

## Design rules

- The shell should talk to `financialanalysis/financial-analyzer/scripts/bondclaw_runtime.py` instead of reading scattered JSON files directly.
- The shell must treat `BondClawRuntime` as its main integration point.
- No default workflow should assume an extra terminal environment.
- The later UI can be Electron, AionUi, or another desktop framework, but the runtime bridge should stay the same.

## Current scope

- Runtime bridge
- Launch helper
- Minimal shell contract
- Home panel model
- 模板中心 panel model
- 信息中心 panel model
- 联系方式面板 model
- 设置面板 model
- Local settings store
- Page registry and navigation model

## Useful entry points

- `launch_bondclaw.py --home`
- `launch_bondclaw.py --settings-panel`
- `launch_bondclaw.py --pages`
- `launch_bondclaw.py --navigation`
- `launch_bondclaw.py --settings`
- `launch_bondclaw.py --prompt-center-panel`
- `launch_bondclaw.py --research-brain-panel`
- `launch_bondclaw.py --lead-capture-panel`
- `launch_bondclaw.py --brand-upgrade-panel`
