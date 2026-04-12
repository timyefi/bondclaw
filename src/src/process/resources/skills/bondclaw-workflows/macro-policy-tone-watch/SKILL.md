---
name: bondclaw-macro-policy-tone-watch
description: 'BondClaw 宏观研究员工作流: policy-tone-watch. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-tone-watch

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕政策表述的语气和措辞变化写一份跟踪笔记，说明是偏宽松、偏中性还是偏收紧，以及这种语气变化对市场预期的影响。要求先判断，再拆语气，再给含义。

## 输入要求

- **date** (必填): string
- **policy_text** (必填): string
- **tone_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- policy_text: "政策表述示例"
- tone_signals: ["强调稳增长","继续关注流动性"]

## 质量检查清单

- [ ] 是否判断政策语气
- [ ] 是否拆解措辞变化
- [ ] 是否给出市场含义
