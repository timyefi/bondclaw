---
name: bondclaw-trader-liquidity-warning
description: 'BondClaw 固收交易员工作流: liquidity-warning. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — liquidity-warning

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、流动性预警和受影响标的，生成一份交易流动性警报。要求说明预警级别、受影响方向、执行建议和需要避免的操作。

## 输入要求

- **date** (必填): string
- **liquidity_warning** (必填): string
- **affected_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- liquidity_warning: "下午资金趋紧"
- affected_list: ["债券A","转债B"]

## 质量检查清单

- [ ] 预警级别是否明确
- [ ] 影响标的是否完整
- [ ] 执行建议是否可操作
- [ ] 是否适合盘中提醒
