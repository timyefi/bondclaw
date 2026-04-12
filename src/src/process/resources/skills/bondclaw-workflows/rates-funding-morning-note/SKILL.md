---
name: bondclaw-rates-funding-morning-note
description: 'BondClaw 利率研究员工作流: funding-morning-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — funding-morning-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、资金面判断和关键利率，生成一份利率晨间提示。要求写清资金松紧、关键利率水平、盘前预期和交易提醒，保持研报写作风格。

## 输入要求

- **date** (必填): string
- **funding_view** (必填): string
- **key_rates** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- funding_view: "略紧"
- key_rates: ["DR007","1D","7D"]

## 质量检查清单

- [ ] 资金判断是否明确
- [ ] 利率水平是否写清
- [ ] 交易提醒是否具体
- [ ] 是否适合晨会快速查看
