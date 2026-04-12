---
name: bondclaw-multi-asset-risk-budget-check
description: 'BondClaw 多资产研究员工作流: risk-budget-check. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — risk-budget-check

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、风险预算和资产列表，生成一份风险预算检查笔记。要求说明各资产的风险占用、是否超配、调整建议和复核节点。

## 输入要求

- **date** (必填): string
- **risk_budget** (必填): string
- **asset_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- risk_budget: "中性偏保守"
- asset_list: ["债券","信用","权益"]

## 质量检查清单

- [ ] 风险预算是否明确
- [ ] 资产占用是否覆盖
- [ ] 调整建议是否可执行
- [ ] 是否适合基金经理查看
