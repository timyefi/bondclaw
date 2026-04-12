---
name: bondclaw-fund-manager-risk-committee-note
description: 'BondClaw 固收基金经理工作流: risk-committee-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — risk-committee-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕风控会议写一份简报，说明本周最重要的风险主题、组合已经采取的动作、还需要继续观察什么。要求适合风控会上直接讲。

## 输入要求

- **date** (必填): string
- **risk_topics** (必填): array
- **portfolio_actions** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- risk_topics: ["久期暴露","信用事件"]
- portfolio_actions: ["缩短部分久期","提升流动性"]

## 质量检查清单

- [ ] 是否明确风险主题
- [ ] 是否说明已采取动作
- [ ] 是否指出继续观察项
