---
name: bondclaw-fund-manager-risk-budget-reset
description: 'BondClaw 固收基金经理工作流: risk-budget-reset. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — risk-budget-reset

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、风险预算状态和约束信号，生成一份风险预算重置说明。要求写清当前风险预算、约束变化、是否需要降风险或调结构，以及下一步核查清单，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **risk_budget_state** (必填): string
- **constraint_flags** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- risk_budget_state: "风险预算接近上限"
- constraint_flags: ["回撤抬升","久期超配"]

## 质量检查清单

- [ ] 风险预算状态是否清楚
- [ ] 约束变化是否明确
- [ ] 动作建议是否具体
- [ ] 是否适合投委或晨会使用
