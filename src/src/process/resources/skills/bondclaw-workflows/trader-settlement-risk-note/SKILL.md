---
name: bondclaw-trader-settlement-risk-note
description: 'BondClaw 固收交易员工作流: settlement-risk-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — settlement-risk-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、结算事项和风险项，生成一份结算风险提示。要求写清待结算事项、风险来源、优先处理顺序和需要立即复核的动作。

## 输入要求

- **date** (必填): string
- **settlement_items** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- settlement_items: ["成交A","成交B"]
- risk_items: ["回执延迟","对账差异"]

## 质量检查清单

- [ ] 待结算事项是否完整
- [ ] 风险来源是否清楚
- [ ] 优先处理顺序是否明确
- [ ] 是否适合收盘前快速查看
