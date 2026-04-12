---
name: bondclaw-convertibles-double-low-screening
description: 'BondClaw 转债研究员工作流: double-low-screening. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — double-low-screening

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

根据转债池和双低条件生成筛选结果，并说明条款、价格、溢价率和事件风险。输出要适合直接用于晨会讨论。

## 输入要求

- **date** (必填): string
- **universe** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- universe: ["可转债A","可转债B"]

## 质量检查清单

- [ ] 是否给出筛选逻辑
- [ ] 是否提示条款风险
- [ ] 是否适合晨会
