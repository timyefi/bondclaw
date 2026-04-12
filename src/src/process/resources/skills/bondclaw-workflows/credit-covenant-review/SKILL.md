---
name: bondclaw-credit-covenant-review
description: 'BondClaw 信用研究员工作流: covenant-review. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — covenant-review

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入发行人、条款和风险关注点，生成一份契约条款审查笔记。要求说明条款要点、潜在触发条件、对持仓和再融资的影响，以及后续跟踪路径。

## 输入要求

- **issuer** (必填): string
- **covenant_terms** (必填): array
- **risk_focus** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- covenant_terms: ["财务约束","回售条款","担保安排"]
- risk_focus: ["现金流","再融资"]

## 质量检查清单

- [ ] 条款要点是否写清
- [ ] 触发条件是否明确
- [ ] 影响是否覆盖持仓
- [ ] 是否适合风控复核
