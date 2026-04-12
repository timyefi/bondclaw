---
name: bondclaw-macro-policy-clarity-note
description: 'BondClaw 宏观研究员工作流: policy-clarity-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-clarity-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策原文和关注主题，生成一份政策表述解读。要求把原文中的关键表述拆成可执行的市场含义，说明短中长端各自可能的反应，并给出后续观察重点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_text** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- policy_text: "稳增长与防风险并重"
- focus_topics: ["政策","利率","风险偏好"]

## 质量检查清单

- [ ] 政策原文是否拆解清楚
- [ ] 市场含义是否落到资产层面
- [ ] 期限反应是否说明
- [ ] 是否适合晨会快速使用
