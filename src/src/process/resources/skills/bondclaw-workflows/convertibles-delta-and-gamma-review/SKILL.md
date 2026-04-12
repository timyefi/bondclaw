---
name: bondclaw-convertibles-delta-and-gamma-review
description: 'BondClaw 转债研究员工作流: delta-and-gamma-review. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — delta-and-gamma-review

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、转债列表和风险关注点，生成一份 delta/gamma 复盘。要求写清正股驱动、弹性变化、仓位含义和交易提醒，保持研报写作风格。

## 输入要求

- **date** (必填): string
- **convertible_list** (必填): array
- **risk_focus** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- convertible_list: ["转债A","转债B"]
- risk_focus: ["正股波动","仓位敏感度"]

## 质量检查清单

- [ ] 弹性变化是否清楚
- [ ] 仓位含义是否明确
- [ ] 交易提醒是否具体
- [ ] 是否适合盘中参考
