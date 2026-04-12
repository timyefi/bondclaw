---
name: bondclaw-rates-liquidity-turn-note
description: 'BondClaw 利率研究员工作流: liquidity-turn-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — liquidity-turn-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、流动性拐点和曲线视角，生成一份流动性拐点说明。要求写清拐点是改善还是恶化、影响最先出现在哪些期限、以及交易窗口是否正在打开，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **liquidity_turn** (必填): string
- **curve_view** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- liquidity_turn: "流动性从偏紧转为中性"
- curve_view: ["中段更活跃","长端承接稳定"]

## 质量检查清单

- [ ] 拐点方向是否明确
- [ ] 期限影响是否清楚
- [ ] 交易窗口是否说明
- [ ] 是否适合交易员和研究员共用
