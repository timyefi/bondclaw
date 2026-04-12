---
name: bondclaw-convertibles-underlying-event-note
description: 'BondClaw 转债研究员工作流: underlying-event-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — underlying-event-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、正股列表和事件描述，生成一份正股事件对转债的影响笔记。要求写清事件性质、正股弹性、对转债估值的传导和交易提醒。

## 输入要求

- **date** (必填): string
- **underlying_list** (必填): array
- **event_description** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- underlying_list: ["正股A","正股B"]
- event_description: "业绩预告上修"

## 质量检查清单

- [ ] 事件性质是否清楚
- [ ] 正股弹性是否说明
- [ ] 对转债的传导是否写明
- [ ] 是否适合盘中使用
