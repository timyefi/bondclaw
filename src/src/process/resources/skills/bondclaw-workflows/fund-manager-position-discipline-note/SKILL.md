---
name: bondclaw-fund-manager-position-discipline-note
description: 'BondClaw 固收基金经理工作流: position-discipline-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — position-discipline-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、持仓状态和纪律信号，生成一份持仓纪律说明。要求写清当前仓位结构、纪律约束、是否需要降风险，以及下一步调仓前应确认的事项，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **position_state** (必填): string
- **discipline_flags** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- position_state: "久期略高、信用中性"
- discipline_flags: ["回撤接近阈值","单券集中度抬升"]

## 质量检查清单

- [ ] 仓位结构是否说明
- [ ] 纪律约束是否明确
- [ ] 调仓确认点是否具体
- [ ] 是否适合投委或晨会使用
