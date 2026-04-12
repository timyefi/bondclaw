---
name: bondclaw-rates-curve-trade-plan
description: 'BondClaw 利率研究员工作流: curve-trade-plan. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-trade-plan

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线分段和交易观点，生成一份利率曲线交易计划。要求包含当前曲线结构、驱动因素、交易思路、止损/止盈与风险提示，写作风格保持研报化、结论先行。

## 输入要求

- **date** (必填): string
- **curve_segments** (必填): array
- **trade_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- curve_segments: ["1Y","5Y","10Y","30Y"]
- trade_view: "关注 5Y-10Y 曲线形态变化"

## 质量检查清单

- [ ] 曲线分段是否写清
- [ ] 交易思路是否可执行
- [ ] 风险控制是否明确
- [ ] 是否适合作为盘前计划
