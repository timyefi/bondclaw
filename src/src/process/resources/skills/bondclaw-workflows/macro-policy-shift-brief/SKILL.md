---
name: bondclaw-macro-policy-shift-brief
description: 'BondClaw 宏观研究员工作流: policy-shift-brief. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — policy-shift-brief

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、政策变化描述和关注主题，生成一份政策变化简报。要求说明政策信号、可能传导路径、对利率/信用/资产配置的影响，以及后续观察重点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **policy_shift** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- policy_shift: "政策表述边际转向稳增长"
- focus_topics: ["政策","利率","信用"]

## 质量检查清单

- [ ] 政策信号是否清楚
- [ ] 传导路径是否完整
- [ ] 影响是否落到资产层面
- [ ] 是否适合晨会快速使用
