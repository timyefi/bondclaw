---
name: bondclaw-macro-policy-demand-note
description: 'BondClaw 宏观研究员工作流: policy-demand-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-demand-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策动作和需求信号，生成一份政策-需求联动观察。要求写清政策如何影响需求、最先反应在哪些资产、以及后续需要验证的需求端信号，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_action** (必填): string
- **demand_signal** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- policy_action: "稳增长政策加码"
- demand_signal: ["信用需求回升","融资需求改善"]

## 质量检查清单

- [ ] 政策与需求的关系是否清楚
- [ ] 资产反应是否明确
- [ ] 验证信号是否具体
- [ ] 是否适合晨会快速使用
