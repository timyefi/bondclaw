---
name: bondclaw-rates-funding-close-note
description: 'BondClaw 利率研究员工作流: funding-close-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — funding-close-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

围绕收盘时点的资金面写一份简短收口，说明今天资金是否平稳、有没有尾盘异常、明天需要盯什么。要求短、准、可直接转发。

## 输入要求

- **date** (必填): string
- **funding_close_readings** (必填): array
- **next_day_watch** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- funding_close_readings: ["隔夜资金平稳","尾盘需求略增"]
- next_day_watch: ["公开市场操作","存单到期量"]

## 质量检查清单

- [ ] 是否总结收盘资金面
- [ ] 是否说明尾盘异常
- [ ] 是否列出次日关注
