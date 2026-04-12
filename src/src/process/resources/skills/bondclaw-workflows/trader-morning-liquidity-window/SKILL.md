---
name: bondclaw-trader-morning-liquidity-window
description: 'BondClaw 固收交易员工作流: morning-liquidity-window. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — morning-liquidity-window

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、流动性判断和待处理交易队列，生成一份晨间流动性提示。要求包含资金判断、执行顺序、优先交易、回执检查和盘中关注项，表达简短直接并保持研报准确性。

## 输入要求

- **date** (必填): string
- **liquidity_view** (必填): string
- **trade_queue** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- liquidity_view: "上午资金略紧"
- trade_queue: ["债券A","债券B","转债C"]

## 质量检查清单

- [ ] 流动性判断是否清楚
- [ ] 执行顺序是否明确
- [ ] 回执检查是否完整
- [ ] 是否适合交易员晨间快速浏览
