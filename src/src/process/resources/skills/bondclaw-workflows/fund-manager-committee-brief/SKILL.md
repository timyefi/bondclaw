---
name: bondclaw-fund-manager-committee-brief
description: 'BondClaw 固收基金经理工作流: committee-brief. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — committee-brief

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入的会议日期、决策点和风险项，生成一份委员会简报。要求分成当前组合状态、需要讨论的决策、主要风险、后续执行安排和复盘节点，语言保持研报写作风格。

## 输入要求

- **committee_date** (必填): string
- **decision_points** (必填): array
- **risk_items** (必填): array

## 输出格式

markdown

## 示例

- committee_date: "2026-04-11"
- decision_points: ["久期调整","信用加减仓","现金头寸安排"]
- risk_items: ["政策变化","资金面波动"]

## 质量检查清单

- [ ] 决策点是否清楚
- [ ] 风险项是否覆盖主要问题
- [ ] 执行安排是否明确
- [ ] 是否适合会议直接宣读
