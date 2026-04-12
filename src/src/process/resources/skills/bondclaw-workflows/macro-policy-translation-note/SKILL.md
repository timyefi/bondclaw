---
name: bondclaw-macro-policy-translation-note
description: 'BondClaw 宏观研究员工作流: policy-translation-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-translation-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策事件和关注主题，输出一份政策传导解读。要求拆成政策原文、市场解读、资金和利率含义、对固收资产的影响、后续观察点五部分，语言保持研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_event** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- policy_event: "公开市场操作与表态更新"
- focus_topics: ["资金面","利率","政策预期"]

## 质量检查清单

- [ ] 政策原文是否准确转述
- [ ] 市场解读是否避免过度延伸
- [ ] 对固收资产影响是否明确
- [ ] 后续观察点是否具体可跟踪
