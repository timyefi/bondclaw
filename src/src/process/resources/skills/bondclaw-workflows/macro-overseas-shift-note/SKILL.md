---
name: bondclaw-macro-overseas-shift-note
description: 'BondClaw 宏观研究员工作流: overseas-shift-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — overseas-shift-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕海外利率、汇率和风险偏好变化写一份简短笔记，说明海外变化如何传导到国内债市和资金面。要求先结论，再机制，再操作含义。

## 输入要求

- **date** (必填): string
- **overseas_signals** (必填): array
- **domestic_implications** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- overseas_signals: ["美债收益率波动","美元指数走强"]
- domestic_implications: ["情绪传导","久期波动"]

## 质量检查清单

- [ ] 是否说明海外变化
- [ ] 是否讲清传导机制
- [ ] 是否落到国内含义
