---
name: bondclaw-multi-asset-correlation-shift-note
description: 'BondClaw 多资产研究员工作流: correlation-shift-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — correlation-shift-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

围绕相关性变化写一份多资产观察，说明哪些资产之间的联动变强或变弱，以及这会怎样影响组合分散效果。先结论，再解释，再给配置含义。

## 输入要求

- **date** (必填): string
- **correlation_changes** (必填): array
- **asset_impacts** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- correlation_changes: ["股债相关性阶段性上升","信用与权益联动增强"]
- asset_impacts: ["分散效果下降","需提升防御性"]

## 质量检查清单

- [ ] 是否说明相关性变化
- [ ] 是否解释组合影响
- [ ] 是否给出配置含义
