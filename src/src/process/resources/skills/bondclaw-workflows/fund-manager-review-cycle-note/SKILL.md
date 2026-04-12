---
name: bondclaw-fund-manager-review-cycle-note
description: 'BondClaw 固收基金经理工作流: review-cycle-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — review-cycle-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、复盘周期和约束信号，生成一份复盘周期说明。要求写清本周期核心变化、约束变化、下一周期重点和需要同步的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **review_cycle** (必填): string
- **constraint_flags** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- review_cycle: "月度复盘"
- constraint_flags: ["回撤抬升","流动性偏紧"]

## 质量检查清单

- [ ] 核心变化是否清楚
- [ ] 约束变化是否明确
- [ ] 下一周期重点是否具体
- [ ] 是否适合投委或晨会使用
