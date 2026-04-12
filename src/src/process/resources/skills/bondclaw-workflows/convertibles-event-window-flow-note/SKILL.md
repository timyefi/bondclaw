---
name: bondclaw-convertibles-event-window-flow-note
description: 'BondClaw 转债研究员工作流: event-window-flow-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — event-window-flow-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、事件窗口和资金流信号，生成一份转债事件窗口资金流观察。要求写清事件窗口如何放大资金行为、对估值和波动的影响，以及盘中最重要的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **event_window** (必填): string
- **flow_signal** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- event_window: "业绩和赎回窗口叠加"
- flow_signal: "资金流入明显"

## 质量检查清单

- [ ] 事件窗口是否清楚
- [ ] 资金行为是否说明
- [ ] 估值波动影响是否提到
- [ ] 是否适合盘中快速查看
