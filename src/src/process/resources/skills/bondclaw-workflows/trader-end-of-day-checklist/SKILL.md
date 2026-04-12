---
name: bondclaw-trader-end-of-day-checklist
description: 'BondClaw 固收交易员工作流: end-of-day-checklist. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — end-of-day-checklist

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

围绕收盘整理交易清单，说明哪些头寸需要确认、哪些结算项需要复核、哪些异动需要留给次日跟踪。要求短、稳、明确。

## 输入要求

- **date** (必填): string
- **close_positions** (必填): array
- **settlement_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- close_positions: ["利率债调仓","信用债减仓"]
- settlement_items: ["成交回执确认","对手方信息核对"]

## 质量检查清单

- [ ] 是否列出收盘待确认事项
- [ ] 是否覆盖结算项
- [ ] 是否便于次日跟踪
