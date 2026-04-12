---
name: bondclaw-convertibles-gamma-swing-note
description: 'BondClaw 转债研究员工作流: gamma-swing-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — gamma-swing-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

围绕 gamma 暴露和正股事件写一份转债短评，说明波动放大对仓位和节奏的影响。要求先判断，再给逻辑，再给风控建议。

## 输入要求

- **date** (必填): string
- **gamma_profile** (必填): string
- **underlying_events** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- gamma_profile: "高 gamma，事件驱动明显"
- underlying_events: ["正股拉升","隐波抬升"]

## 质量检查清单

- [ ] 是否说明 gamma 特征
- [ ] 是否关联正股事件
- [ ] 是否给出风控建议
