---
name: bondclaw-convertibles-event-window-note
description: 'BondClaw 转债研究员工作流: event-window-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — event-window-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

围绕事件窗口写一份转债观察，说明事件发生前后应该如何调整关注顺序和交易节奏。要求先判断，再解释，再给执行建议。

## 输入要求

- **date** (必填): string
- **event_window** (必填): string
- **candidate_bonds** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- event_window: "未来两周"
- candidate_bonds: ["可转债A","可转债B"]

## 质量检查清单

- [ ] 是否说明事件窗口
- [ ] 是否给出关注顺序
- [ ] 是否有执行建议
