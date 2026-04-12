---
name: bondclaw-fund-manager-portfolio-risk-review
description: 'BondClaw 固收基金经理工作流: portfolio-risk-review. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — portfolio-risk-review

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入复核日期、组合状态和风险信号，生成一份组合风险复盘。要求拆分头寸、收益、回撤、风险暴露和下一步调整建议。

## 输入要求

- **review_date** (必填): string
- **portfolio_status** (必填): string
- **risk_signals** (必填): array

## 输出格式

markdown

## 示例

- review_date: "2026-04-11"
- portfolio_status: "中性偏防守"
- risk_signals: ["利率上行","信用分化"]

## 质量检查清单

- [ ] 组合状态是否清楚
- [ ] 风险暴露是否覆盖
- [ ] 调整建议是否明确
- [ ] 是否适合投委会复盘
