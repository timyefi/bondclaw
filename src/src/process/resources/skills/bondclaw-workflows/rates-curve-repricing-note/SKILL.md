---
name: bondclaw-rates-curve-repricing-note
description: 'BondClaw 利率研究员工作流: curve-repricing-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-repricing-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线变动和市场背景，生成一份曲线重定价点评。要求覆盖曲线结构变化、驱动因素、交易含义、后续观察点和风险提示，语言保持研报化。

## 输入要求

- **date** (必填): string
- **curve_move** (必填): string
- **market_context** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- curve_move: "5Y 与 10Y 利差收窄"
- market_context: ["招标结果","资金面波动","政策预期变化"]

## 质量检查清单

- [ ] 曲线变动是否明确
- [ ] 驱动因素是否准确
- [ ] 交易含义是否可执行
- [ ] 是否能直接给交易员参考
