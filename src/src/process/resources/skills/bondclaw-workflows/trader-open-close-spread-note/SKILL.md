---
name: bondclaw-trader-open-close-spread-note
description: 'BondClaw 固收交易员工作流: open-close-spread-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — open-close-spread-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、开收盘价差和风险项，生成一份开收盘价差提示。要求写清开盘和收盘的差异、是否存在异常、可能的撮合或流动性原因，以及需要复核的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **open_close_spread** (必填): string
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- open_close_spread: "收盘价明显高于开盘"
- risk_items: ["成交稀疏","报价跳变"]

## 质量检查清单

- [ ] 开收盘差异是否说清
- [ ] 异常原因是否具体
- [ ] 复核动作是否明确
- [ ] 是否适合盘中快速查看
