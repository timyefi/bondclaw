---
name: bondclaw-credit-issuer-deep-dive
description: 'BondClaw 信用研究员工作流: issuer-deep-dive. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — issuer-deep-dive

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕发行主体做深度信用分析，优先检查财务结构、债务压力、现金流、受限资金、担保与或有事项。必须先结论，再证据，再风险。

## 输入要求

- **issuer** (必填): string
- **reporting_period** (必填): string

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- reporting_period: "2025A"

## 质量检查清单

- [ ] 是否包含主体结论
- [ ] 是否引用附注证据
- [ ] 是否覆盖核心风险点
