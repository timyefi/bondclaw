---
name: bondclaw-convertibles-premium-stability-note
description: 'BondClaw 转债研究员工作流: premium-stability-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — premium-stability-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、转债溢价水平和稳定性信号，生成一份转债稳定性观察。要求写清估值安全边际、波动来源、正股与转债联动，以及适合的跟踪动作。

## 输入要求

- **date** (必填): string
- **premium_level** (必填): string
- **stability_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- premium_level: "中等偏高"
- stability_signals: ["正股横盘","成交活跃","溢价波动收敛"]

## 质量检查清单

- [ ] 估值与波动是否都提到
- [ ] 正股联动是否说明
- [ ] 跟踪动作是否具体
- [ ] 是否适合盘中快速查看
