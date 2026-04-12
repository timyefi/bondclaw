---
name: bondclaw-macro-policy-event-wrap
description: 'BondClaw 宏观研究员工作流: policy-event-wrap. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-event-wrap

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕当天政策事件写一份简短复盘，先给结论，再给政策含义、市场反馈、对债市和资金面的影响。文风保持克制、清晰、可转发。

## 输入要求

- **date** (必填): string
- **policy_event** (必填): string
- **market_reaction** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- policy_event: "央行公开市场操作"
- market_reaction: ["短端资金利率回落","长端收益率小幅震荡"]

## 质量检查清单

- [ ] 是否先给政策结论
- [ ] 是否解释市场反应
- [ ] 是否落到债市和资金面
