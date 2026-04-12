---
name: bondclaw-convertibles-arbitrage-note
description: 'BondClaw 转债研究员工作流: arbitrage-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — arbitrage-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、套利组合和定价观点，生成一份转债套利笔记。要求说明价差来源、套利空间、主要风险和执行提示。

## 输入要求

- **date** (必填): string
- **arbitrage_pair** (必填): array
- **pricing_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- arbitrage_pair: ["正股A","转债A"]
- pricing_view: "价差偏宽"

## 质量检查清单

- [ ] 套利组合是否明确
- [ ] 价差来源是否写清
- [ ] 风险是否充分
- [ ] 是否适合盘前决策
