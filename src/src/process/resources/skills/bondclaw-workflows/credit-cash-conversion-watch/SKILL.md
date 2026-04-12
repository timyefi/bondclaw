---
name: bondclaw-credit-cash-conversion-watch
description: 'BondClaw 信用研究员工作流: cash-conversion-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — cash-conversion-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕主体现金转化效率写一份观察笔记，说明经营现金流、营运资本变化和利润质量之间的关系。先结论，再证据，再风险。

## 输入要求

- **issuer** (必填): string
- **operating_cash_flow** (必填): string
- **working_capital_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- operating_cash_flow: "经营现金流转弱"
- working_capital_signals: ["应收增加","存货抬升"]

## 质量检查清单

- [ ] 是否说明现金转化
- [ ] 是否解释营运资本变化
- [ ] 是否给出风险判断
