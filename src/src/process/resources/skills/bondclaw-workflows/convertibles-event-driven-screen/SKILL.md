---
name: bondclaw-convertibles-event-driven-screen
description: 'BondClaw 转债研究员工作流: event-driven-screen. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — event-driven-screen

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

根据事件催化和条款条件，筛选可能出现弹性的转债标的。输出应说明触发事件、核心条款、风格偏好和风险约束。

## 输入要求

- **date** (必填): string
- **event_candidates** (必填): array
- **screen_rules** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- event_candidates: ["业绩预告改善","正股放量突破"]
- screen_rules: ["双低优先","条款风险可控"]

## 质量检查清单

- [ ] 是否点明事件催化
- [ ] 是否结合条款和价格
- [ ] 是否给出风险约束
