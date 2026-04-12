---
name: bondclaw-macro-inflation-implication-note
description: 'BondClaw 宏观研究员工作流: inflation-implication-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — inflation-implication-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕通胀读数写一份影响说明，判断数据对利率预期、资金面和政策判断意味着什么。要求先给结论，再讲结构，再落到债市含义。

## 输入要求

- **date** (必填): string
- **inflation_reading** (必填): string
- **market_expectation** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- inflation_reading: "通胀读数温和"
- market_expectation: "市场原本预期持平"

## 质量检查清单

- [ ] 是否判断通胀对预期的影响
- [ ] 是否说明结构变化
- [ ] 是否落到债市含义
