---
name: bondclaw-trader-reconciliation-closeout-note
description: 'BondClaw 固收交易员工作流: reconciliation-closeout-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — reconciliation-closeout-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、对账事项和风险项，生成一份对账收尾说明。要求写清对账对象、差异来源、优先处理顺序和需要留档的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **reconciliation_items** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- reconciliation_items: ["成交回执","资金回单"]
- risk_items: ["差异未闭合","回执滞后"]

## 质量检查清单

- [ ] 对账对象是否清楚
- [ ] 差异来源是否明确
- [ ] 处理顺序是否合理
- [ ] 是否适合收盘前快速查看
