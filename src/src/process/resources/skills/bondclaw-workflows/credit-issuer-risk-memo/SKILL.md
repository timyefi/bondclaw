---
name: bondclaw-credit-issuer-risk-memo
description: 'BondClaw 信用研究员工作流: issuer-risk-memo. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — issuer-risk-memo

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

针对输入发行人和风险信号，生成一份信用风险备忘录。要求先给出风险结论，再拆解财务、流动性、债务结构、事件催化和后续验证路径，全文保持研报写作风格。

## 输入要求

- **issuer** (必填): string
- **date** (必填): string
- **risk_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- date: "2026-04-10"
- risk_signals: ["偿债压力","融资收紧","担保变化"]

## 质量检查清单

- [ ] 风险结论是否先行
- [ ] 信号是否有证据链
- [ ] 后续验证路径是否明确
- [ ] 是否便于直接发给基金经理
