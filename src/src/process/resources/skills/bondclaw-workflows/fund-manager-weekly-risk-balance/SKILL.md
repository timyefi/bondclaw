---
name: bondclaw-fund-manager-weekly-risk-balance
description: 'BondClaw 固收基金经理工作流: weekly-risk-balance. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — weekly-risk-balance

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕一周的风险预算和收益驱动做平衡复盘，说明哪些风险消耗了预算、哪些策略贡献了收益、下周该怎么调。要求简洁但要可执行。

## 输入要求

- **date** (必填): string
- **risk_buckets** (必填): array
- **return_drivers** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- risk_buckets: ["久期风险","信用风险","流动性风险"]
- return_drivers: ["票息贡献","久期交易"]

## 质量检查清单

- [ ] 是否覆盖风险预算
- [ ] 是否说明收益来源
- [ ] 是否提出下周调整
