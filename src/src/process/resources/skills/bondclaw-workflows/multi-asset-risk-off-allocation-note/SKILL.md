---
name: bondclaw-multi-asset-risk-off-allocation-note
description: 'BondClaw 多资产研究员工作流: risk-off-allocation-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — risk-off-allocation-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

在风险偏好转弱时生成配置提示，说明需要向哪些资产收缩风险、哪些资产更适合作为防御性配置。先结论，再拆信号，再给动作。

## 输入要求

- **date** (必填): string
- **risk_off_signals** (必填): array
- **allocation_changes** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- risk_off_signals: ["海外波动上升","权益回撤扩大"]
- allocation_changes: ["提升利率债占比","降低高弹性资产"]

## 质量检查清单

- [ ] 是否识别风险偏好变化
- [ ] 是否给出防御方向
- [ ] 是否落到配置动作
