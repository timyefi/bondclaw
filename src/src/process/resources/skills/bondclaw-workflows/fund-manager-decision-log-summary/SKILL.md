---
name: bondclaw-fund-manager-decision-log-summary
description: 'BondClaw 固收基金经理工作流: decision-log-summary. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — decision-log-summary

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、决策事项和后续事项，生成一份决策日志总结。要求按决策、理由、执行和后续跟进四部分组织，保证团队内部可追溯。

## 输入要求

- **date** (必填): string
- **decision_items** (必填): array
- **followup_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- decision_items: ["减久期","加信用观察"]
- followup_items: ["检查资金面","复核风险敞口"]

## 质量检查清单

- [ ] 决策事项是否完整
- [ ] 理由是否清楚
- [ ] 后续跟进是否明确
- [ ] 是否便于内部留档
