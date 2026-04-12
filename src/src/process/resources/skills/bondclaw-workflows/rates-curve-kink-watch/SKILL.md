---
name: bondclaw-rates-curve-kink-watch
description: 'BondClaw 利率研究员工作流: curve-kink-watch. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-kink-watch

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线拐点和驱动摘要，生成一份曲线拐点观察。要求写清拐点出现在哪些期限、背后的供需和资金驱动、以及最适合关注的交易窗口，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **curve_kink** (必填): string
- **driver_summary** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- curve_kink: "5Y附近出现拐点"
- driver_summary: ["中端需求增强","长端承接稳定"]

## 质量检查清单

- [ ] 拐点位置是否明确
- [ ] 驱动因素是否完整
- [ ] 交易窗口是否说清
- [ ] 是否适合交易员和研究员共用
