---
name: bondclaw-trader-inventory-risk-note
description: 'BondClaw 固收交易员工作流: inventory-risk-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — inventory-risk-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、库存状态和风险项，生成一份库存风险提示。要求写清库存暴露、可能的结算/流动性/价差风险，以及优先处理顺序，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **inventory_state** (必填): string
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- inventory_state: "短久期库存偏多"
- risk_items: ["价差回撤","成交稀疏","结算冲突"]

## 质量检查清单

- [ ] 库存暴露是否清楚
- [ ] 风险是否分层
- [ ] 优先处理顺序是否明确
- [ ] 是否适合盘前快速查看
