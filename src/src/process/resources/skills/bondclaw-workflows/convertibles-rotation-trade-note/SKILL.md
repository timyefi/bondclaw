---
name: bondclaw-convertibles-rotation-trade-note
description: 'BondClaw 转债研究员工作流: rotation-trade-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — rotation-trade-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

围绕风格轮动写一份转债交易笔记，说明轮动主题、候选标的、入场逻辑和回撤控制。先给结论，再给排序，再给执行建议。

## 输入要求

- **date** (必填): string
- **rotation_theme** (必填): string
- **candidate_bonds** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- rotation_theme: "低波动切高弹性"
- candidate_bonds: ["可转债A","可转债B"]

## 质量检查清单

- [ ] 是否说明轮动主题
- [ ] 是否排序候选标的
- [ ] 是否给出回撤控制
