---
name: bondclaw-rates-term-spread-watch
description: 'BondClaw 利率研究员工作流: term-spread-watch. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — term-spread-watch

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

根据期限利差、资金面信号和曲线结构，判断期限价差是否出现可交易机会。先给判断，再给背后驱动，最后给交易含义和风险。

## 输入要求

- **date** (必填): string
- **term_spreads** (必填): array
- **liquidity_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- term_spreads: ["1Y-10Y","5Y-10Y"]
- liquidity_signals: ["DR007稳定","同业存单发行放量"]

## 质量检查清单

- [ ] 是否给出期限利差判断
- [ ] 是否连接资金面与曲线
- [ ] 是否说明交易风险
