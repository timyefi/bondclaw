---
name: bondclaw-trader-settlement-followup-note
description: 'BondClaw 固收交易员工作流: settlement-followup-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — settlement-followup-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

围绕结算跟进写一份简短提醒，说明哪些成交需要回执确认、哪些对手方需要继续跟进、哪些事项要留到明天处理。输出短而明确，便于收盘后执行。

## 输入要求

- **date** (必填): string
- **settlement_items** (必填): array
- **pending_counterparties** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- settlement_items: ["成交回执待确认","资金划拨待复核"]
- pending_counterparties: ["对手方A","对手方B"]

## 质量检查清单

- [ ] 是否列出回执确认项
- [ ] 是否列出待跟进对手方
- [ ] 是否适合收盘后执行
