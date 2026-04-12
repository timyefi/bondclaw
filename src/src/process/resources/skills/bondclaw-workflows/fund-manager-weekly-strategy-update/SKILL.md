---
name: bondclaw-fund-manager-weekly-strategy-update
description: 'BondClaw 固收基金经理工作流: weekly-strategy-update. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — weekly-strategy-update

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入周起点、策略重点和风险项，生成一份周度策略更新。要求说明本周策略重心、组合动作、风控关注和复盘节点，保持研报写作风格。

## 输入要求

- **week_start** (必填): string
- **strategy_focus** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- week_start: "2026-04-13"
- strategy_focus: ["久期控制","信用分层","现金管理"]
- risk_items: ["政策变化","流动性收缩"]

## 质量检查清单

- [ ] 策略重点是否明确
- [ ] 组合动作是否可执行
- [ ] 风险项是否覆盖
- [ ] 是否适合周会上直接说明
