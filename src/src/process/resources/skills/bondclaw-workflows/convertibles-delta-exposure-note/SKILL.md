---
name: bondclaw-convertibles-delta-exposure-note
description: 'BondClaw 转债研究员工作流: delta-exposure-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — delta-exposure-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

根据持仓的 delta 暴露和正股变动，判断组合当前对行情的敏感度，并给出是否需要调节仓位的建议。要求先判断，再解释，再给动作。

## 输入要求

- **date** (必填): string
- **position_profile** (必填): string
- **underlying_moves** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- position_profile: "偏高 delta，集中在成长风格"
- underlying_moves: ["正股放量上行","波动率抬升"]

## 质量检查清单

- [ ] 是否说明 delta 暴露
- [ ] 是否结合正股变化
- [ ] 是否给出仓位动作
