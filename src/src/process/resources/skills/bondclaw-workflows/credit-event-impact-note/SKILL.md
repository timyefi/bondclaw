---
name: bondclaw-credit-event-impact-note
description: 'BondClaw 信用研究员工作流: event-impact-note. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — event-impact-note

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕信用事件写一份影响评估，说明事件如何影响主体偿债能力、市场情绪和再融资路径。输出要求先结论，再拆影响渠道，再给风险提示。

## 输入要求

- **issuer** (必填): string
- **event_summary** (必填): string
- **impact_channels** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- event_summary: "信用事件简述"
- impact_channels: ["再融资压力","市场情绪传导"]

## 质量检查清单

- [ ] 是否说明事件影响
- [ ] 是否拆解影响渠道
- [ ] 是否提示风险升级
