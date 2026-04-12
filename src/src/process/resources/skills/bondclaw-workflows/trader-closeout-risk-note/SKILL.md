---
name: bondclaw-trader-closeout-risk-note
description: 'BondClaw 固收交易员工作流: closeout-risk-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — closeout-risk-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、收尾事项和风险项，生成一份收盘收尾风险提示。要求写清待收尾事项、可能卡点、优先处理顺序和次日需要承接的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **closeout_items** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- closeout_items: ["成交确认","回执核对"]
- risk_items: ["对账延迟","回款未确认"]

## 质量检查清单

- [ ] 收尾事项是否完整
- [ ] 卡点是否明确
- [ ] 优先顺序是否清楚
- [ ] 是否适合收盘前快速查看
