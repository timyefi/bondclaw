---
name: bondclaw-credit-leverage-watch
description: 'BondClaw 信用研究员工作流: leverage-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — leverage-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕杠杆水平写一份跟踪笔记，说明债务杠杆、期限结构和再融资压力的变化。先给结论，再列指标，再给风险提示。

## 输入要求

- **issuer** (必填): string
- **leverage_metrics** (必填): string
- **debt_structure** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- leverage_metrics: "杠杆水平偏高"
- debt_structure: ["短债占比高","中长期债务压力上升"]

## 质量检查清单

- [ ] 是否说明杠杆变化
- [ ] 是否列出期限结构
- [ ] 是否提示再融资压力
