---
name: bondclaw-rates-steepness-watch
description: 'BondClaw 利率研究员工作流: steepness-watch. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — steepness-watch

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线陡峭度和驱动摘要，生成一份曲线陡峭度观察。要求说明陡峭化或平坦化的主要来源、不同期限的相对机会、以及需要防范的反向波动风险。

## 输入要求

- **date** (必填): string
- **curve_steepness** (必填): string
- **driver_summary** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- curve_steepness: "前陡后平"
- driver_summary: ["短端资金偏紧","长端需求稳定"]

## 质量检查清单

- [ ] 曲线形态是否清楚
- [ ] 驱动因素是否完整
- [ ] 期限机会是否明确
- [ ] 风险提示是否具体
