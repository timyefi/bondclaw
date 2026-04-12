---
name: bondclaw-trader-post-close-risk-note
description: 'BondClaw 固收交易员工作流: post-close-risk-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — post-close-risk-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、收盘后事项和风险项，生成一份盘后风险提示。要求写清收盘后还要完成什么、哪类风险最需要留档、第二天最先承接的动作是什么，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **post_close_items** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- post_close_items: ["未完成回执","待确认成交"]
- risk_items: ["差异未闭合","结算延迟"]

## 质量检查清单

- [ ] 盘后事项是否完整
- [ ] 风险留档是否清楚
- [ ] 次日承接动作是否明确
- [ ] 是否适合交易员收尾查看
