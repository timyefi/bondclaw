---
name: bondclaw-fund-manager-morning-meeting-pack
description: 'BondClaw 固收基金经理工作流: morning-meeting-pack. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — morning-meeting-pack

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

为固收基金经理生成晨会包，覆盖市场回顾、风险点、今日关注和仓位建议。要求简短、结论优先、可直接开会使用。

## 输入要求

- **date** (必填): string
- **portfolio_focus** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- portfolio_focus: ["久期","信用","流动性"]

## 质量检查清单

- [ ] 是否适合晨会阅读
- [ ] 是否覆盖仓位建议
- [ ] 是否包含关键风险
