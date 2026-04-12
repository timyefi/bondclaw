---
name: bondclaw-trader-morning-execution-checklist
description: 'BondClaw 固收交易员工作流: morning-execution-checklist. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — morning-execution-checklist

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

根据库存和市场风险生成早盘执行清单，优先列出需要先处理的头寸、对手方、报价和风控事项。输出必须短、准、可直接开工。

## 输入要求

- **date** (必填): string
- **inventory_snapshot** (必填): array
- **market_risks** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- inventory_snapshot: ["利率债久期偏长","信用债余额较多"]
- market_risks: ["资金面波动","尾盘成交放大"]

## 质量检查清单

- [ ] 是否列出优先处理项
- [ ] 是否覆盖对手方和风控
- [ ] 是否适合早盘直接执行
