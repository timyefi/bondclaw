---
name: bondclaw-macro-policy-watch
description: 'BondClaw 宏观研究员工作流: policy-watch. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-watch

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策摘要和关注主题，生成一份政策观察笔记。要求先给判断，再拆政策方向、市场反馈、资金和利率含义、后续观察点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_summary** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- policy_summary: "公开市场操作节奏变化"
- focus_topics: ["资金面","政策预期","利率"]

## 质量检查清单

- [ ] 政策摘要是否清楚
- [ ] 判断是否先行
- [ ] 市场反馈是否准确
- [ ] 是否适合晨会直读
