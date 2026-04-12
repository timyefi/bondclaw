---
name: bondclaw-fund-manager-portfolio-shift-note
description: 'BondClaw 固收基金经理工作流: portfolio-shift-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — portfolio-shift-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、组合变化和约束信号，生成一份组合变化说明。要求写清调仓方向、约束原因、后续承接动作和需要同步给投委的内容，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **portfolio_shift** (必填): string
- **constraint_flags** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- portfolio_shift: "缩短久期、提高信用分散度"
- constraint_flags: ["回撤压力","流动性约束"]

## 质量检查清单

- [ ] 调仓方向是否清楚
- [ ] 约束原因是否明确
- [ ] 承接动作是否具体
- [ ] 是否适合投委或晨会使用
