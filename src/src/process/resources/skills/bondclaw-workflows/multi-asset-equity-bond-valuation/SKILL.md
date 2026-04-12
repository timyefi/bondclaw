---
name: bondclaw-multi-asset-equity-bond-valuation
description: 'BondClaw 多资产研究员工作流: equity-bond-valuation. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — equity-bond-valuation

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、权益观点和债券观点，生成一份股债估值对比笔记。要求说明估值差、风险偏好和资产切换含义，并给出组合动作建议。

## 输入要求

- **date** (必填): string
- **equity_view** (必填): string
- **bond_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- equity_view: "偏震荡"
- bond_view: "偏中性"

## 质量检查清单

- [ ] 股债观点是否清楚
- [ ] 估值差是否有说明
- [ ] 组合动作是否明确
- [ ] 是否便于配置讨论
