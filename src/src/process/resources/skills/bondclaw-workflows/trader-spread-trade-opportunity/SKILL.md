---
name: bondclaw-trader-spread-trade-opportunity
description: 'BondClaw 固收交易员工作流: spread-trade-opportunity. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — spread-trade-opportunity

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、利差候选和执行观点，生成一份利差交易机会提示。要求说明机会来源、执行顺序、风险点和盘中观察项。

## 输入要求

- **date** (必填): string
- **spread_candidates** (必填): array
- **execution_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- spread_candidates: ["国开-国债","信用-利率"]
- execution_view: "偏短线"

## 质量检查清单

- [ ] 利差机会是否明确
- [ ] 执行顺序是否合理
- [ ] 风险点是否清楚
- [ ] 是否适合盘中决策
