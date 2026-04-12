---
name: bondclaw-fund-manager-overnight-brief
description: 'BondClaw 固收基金经理工作流: overnight-brief. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — overnight-brief

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕夜间发生的海外和国内事件写一份隔夜简报，说明哪些事件会影响第二天组合判断、哪些标的需要优先观察。要求短、准、能接晨会。

## 输入要求

- **date** (必填): string
- **overnight_events** (必填): array
- **portfolio_watchlist** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- overnight_events: ["海外利率上行","国内政策消息"]
- portfolio_watchlist: ["利率久期","信用敞口"]

## 质量检查清单

- [ ] 是否抓住隔夜事件
- [ ] 是否对应到持仓关注点
- [ ] 是否能接晨会
