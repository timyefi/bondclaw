---
name: bondclaw-rates-yield-spread-opportunity
description: 'BondClaw 利率研究员工作流: yield-spread-opportunity. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — yield-spread-opportunity

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、利差候选和利率观点，生成一份利差机会提示。要求说明可交易的利差对、驱动逻辑、风险点和执行提示，保持研报写作风格。

## 输入要求

- **date** (必填): string
- **spread_candidates** (必填): array
- **rate_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- spread_candidates: ["1Y-5Y","5Y-10Y"]
- rate_view: "区间震荡"

## 质量检查清单

- [ ] 候选利差是否具体
- [ ] 交易逻辑是否完整
- [ ] 风险点是否明确
- [ ] 是否适合盘前查看
