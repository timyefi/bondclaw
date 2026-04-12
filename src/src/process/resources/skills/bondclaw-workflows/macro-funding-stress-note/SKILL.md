---
name: bondclaw-macro-funding-stress-note
description: 'BondClaw 宏观研究员工作流: funding-stress-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — funding-stress-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、资金压力描述和关注主题，生成一份资金压力观察。要求说明压力从哪里来、会传导到哪些期限和资产、以及需要优先跟踪的缓解信号，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **funding_stress** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- funding_stress: "跨月资金偏紧"
- focus_topics: ["资金","利率","信用"]

## 质量检查清单

- [ ] 压力来源是否清楚
- [ ] 传导链条是否完整
- [ ] 缓解信号是否明确
- [ ] 是否适合晨会快速使用
