---
name: bondclaw-fund-manager-week-ahead-playbook
description: 'BondClaw 固收基金经理工作流: week-ahead-playbook. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — week-ahead-playbook

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入的周度起点、组合优先项和风险项，生成一份周前交易和研究播放单。要求包含本周重点、组合动作、观察信号、风控提醒和周内复盘节点，保持研报写作风格。

## 输入要求

- **week_start** (必填): string
- **portfolio_priorities** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- week_start: "2026-04-13"
- portfolio_priorities: ["久期控制","信用分层","现金管理"]
- risk_items: ["政策变化","流动性收缩"]

## 质量检查清单

- [ ] 本周重点是否明确
- [ ] 组合动作是否可执行
- [ ] 风控提醒是否覆盖关键风险
- [ ] 是否适合周会直接使用
