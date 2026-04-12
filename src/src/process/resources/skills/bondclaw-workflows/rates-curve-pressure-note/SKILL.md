---
name: bondclaw-rates-curve-pressure-note
description: 'BondClaw 利率研究员工作流: curve-pressure-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-pressure-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线压力和驱动摘要，生成一份曲线压力观察。要求说明压力体现在哪些期限、背后的资金或供需因素、以及可能的交易应对方式，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **curve_pressure** (必填): string
- **driver_summary** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- curve_pressure: "中长端承压"
- driver_summary: ["供给偏多","需求犹豫"]

## 质量检查清单

- [ ] 压力期限是否说清
- [ ] 驱动因素是否完整
- [ ] 应对方式是否明确
- [ ] 是否适合交易员和研究员共用
