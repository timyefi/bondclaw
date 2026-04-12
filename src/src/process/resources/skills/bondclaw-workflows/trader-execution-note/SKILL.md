---
name: bondclaw-trader-execution-note
description: 'BondClaw 固收交易员工作流: execution-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — execution-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

根据交易清单和市场变化，生成交易执行备注，说明成交、滑点、异常和后续观察重点。输出需简洁、可追踪。

## 输入要求

- **date** (必填): string
- **trade_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- trade_list: ["买入利率债","减仓信用债"]

## 质量检查清单

- [ ] 是否记录交易动作
- [ ] 是否说明异常
- [ ] 是否适合回看
