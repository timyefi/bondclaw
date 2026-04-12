---
name: bondclaw-macro-funding-migration-note
description: 'BondClaw 宏观研究员工作流: funding-migration-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — funding-migration-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、资金迁移描述和关注主题，生成一份资金迁移观察。要求写清资金从哪里来、流向哪里、对利率和信用的影响以及后续观察点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **funding_shift** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- funding_shift: "短端资金向中长端传导"
- focus_topics: ["资金面","利率","信用"]

## 质量检查清单

- [ ] 资金迁移是否说清
- [ ] 对利率和信用的含义是否明确
- [ ] 后续观察点是否具体
- [ ] 是否适合晨会快速使用
