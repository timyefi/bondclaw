---
name: bondclaw-trader-intraday-liquidity-note
description: 'BondClaw 固收交易员工作流: intraday-liquidity-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — intraday-liquidity-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

围绕盘中流动性变化写一份短提示，说明哪类资产成交开始变慢、哪些报价需要优先处理、是否需要提前做风险动作。要求足够短，便于盘中直接看。

## 输入要求

- **date** (必填): string
- **intraday_signals** (必填): array
- **liquidity_actions** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- intraday_signals: ["上午成交偏快","午后流动性收缩"]
- liquidity_actions: ["优先处理大额买盘","控制低流动性持仓"]

## 质量检查清单

- [ ] 是否说明盘中流动性变化
- [ ] 是否给出处理优先级
- [ ] 是否提示风险动作
