---
name: bondclaw-convertibles-earnings-event-note
description: 'BondClaw 转债研究员工作流: earnings-event-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — earnings-event-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、主体名称和业绩事件，生成一份转债业绩事件观察。要求写清业绩预期、可能的正股反应、转债估值联动和适合的跟踪动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **earnings_event** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- earnings_event: "业绩预告边际改善"

## 质量检查清单

- [ ] 业绩事件是否说清
- [ ] 正股联动是否提到
- [ ] 转债估值反应是否说明
- [ ] 是否适合盘中快速查看
