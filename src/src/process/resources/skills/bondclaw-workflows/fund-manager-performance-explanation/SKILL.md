---
name: bondclaw-fund-manager-performance-explanation
description: 'BondClaw 固收基金经理工作流: performance-explanation. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — performance-explanation

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入周期、业绩原因和驱动项，生成一份业绩解释说明。要求写清收益来源、拖累项、可复制经验和后续优化方向，全文保持研报写作风格。

## 输入要求

- **period** (必填): string
- **performance_reason** (必填): string
- **key_drivers** (必填): array

## 输出格式

markdown

## 示例

- period: "2026Q1"
- performance_reason: "利率方向判断正确"
- key_drivers: ["久期","信用分层"]

## 质量检查清单

- [ ] 收益来源是否写清
- [ ] 拖累项是否覆盖
- [ ] 经验是否可复制
- [ ] 是否适合对外解释
