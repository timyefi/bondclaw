---
name: bondclaw-trader-deal-anomaly-check
description: 'BondClaw 固收交易员工作流: deal-anomaly-check. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — deal-anomaly-check

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、交易清单和异常信号，生成一份成交异常检查笔记。要求说明异常位置、可能原因、是否影响结算和需要立刻复核的内容。

## 输入要求

- **date** (必填): string
- **deal_list** (必填): array
- **anomaly_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- deal_list: ["成交A","成交B"]
- anomaly_signals: ["价格偏离","数量异常"]

## 质量检查清单

- [ ] 异常是否写清
- [ ] 可能原因是否合理
- [ ] 结算影响是否说明
- [ ] 是否适合交易员快速查看
