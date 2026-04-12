---
name: bondclaw-rates-interbank-liquidity-check
description: 'BondClaw 利率研究员工作流: interbank-liquidity-check. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — interbank-liquidity-check

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、同业流动性快照和市场背景，生成一份同业流动性检查笔记。要求说明资金松紧、主要驱动、对短端和曲线的含义，以及当日交易关注点。

## 输入要求

- **date** (必填): string
- **liquidity_snapshot** (必填): string
- **market_context** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- liquidity_snapshot: "隔夜偏紧，7D 偏平"
- market_context: ["缴税","逆回购到期"]

## 质量检查清单

- [ ] 流动性快照是否准确
- [ ] 驱动因素是否明确
- [ ] 对曲线含义是否写明
- [ ] 是否适合交易员参考
