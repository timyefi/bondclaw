---
name: bondclaw-rates-funding-curve-guard
description: 'BondClaw 利率研究员工作流: funding-curve-guard. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — funding-curve-guard

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、资金面状态和曲线视角，生成一份资金-曲线联动观察。要求说明资金约束如何改变曲线交易窗口、哪些期限最敏感、以及需要回避的风险点。

## 输入要求

- **date** (必填): string
- **funding_condition** (必填): string
- **curve_view** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- funding_condition: "短端资金偏紧"
- curve_view: ["中段陡峭","长端偏平"]

## 质量检查清单

- [ ] 资金条件是否明确
- [ ] 曲线敏感区是否准确
- [ ] 交易窗口是否说清
- [ ] 是否适合交易员和研究员共用
