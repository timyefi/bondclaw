---
name: bondclaw-macro-policy-implementation-note
description: 'BondClaw 宏观研究员工作流: policy-implementation-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-implementation-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策落地措施和关注主题，生成一份政策落地观察。要求写清政策如何实施、最先影响哪些变量、市场会如何重新定价，以及后续需要验证的信号，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_measure** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- policy_measure: "降准并配合窗口指导"
- focus_topics: ["政策","流动性","利率"]

## 质量检查清单

- [ ] 实施路径是否说清
- [ ] 影响变量是否明确
- [ ] 市场定价逻辑是否完整
- [ ] 是否适合晨会快速使用
