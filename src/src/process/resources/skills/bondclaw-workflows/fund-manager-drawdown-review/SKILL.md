---
name: bondclaw-fund-manager-drawdown-review
description: 'BondClaw 固收基金经理工作流: drawdown-review. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — drawdown-review

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕组合回撤做一份复盘，说明回撤来源、暴露方向、应对动作和后续修复路径。要求先结论，再拆因，再给管理建议。

## 输入要求

- **date** (必填): string
- **drawdown_window** (必填): string
- **portfolio_changes** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- drawdown_window: "近五个交易日"
- portfolio_changes: ["利率久期偏长","信用仓位集中"]

## 质量检查清单

- [ ] 是否说明回撤来源
- [ ] 是否给出应对动作
- [ ] 是否提出后续修复路径
