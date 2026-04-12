---
name: bondclaw-credit-liquidity-pressure-note
description: 'BondClaw 信用研究员工作流: liquidity-pressure-note. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — liquidity-pressure-note

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕主体流动性压力做快速备忘，说明触发事件、现金流缓冲、再融资路径和后续观察点。要求直接、简洁、可用于内部风险提醒。

## 输入要求

- **issuer** (必填): string
- **liquidity_events** (必填): array
- **latest_cash_profile** (必填): string

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- liquidity_events: ["短债集中到期","融资渠道收缩"]
- latest_cash_profile: "账面现金覆盖率下降"

## 质量检查清单

- [ ] 是否明确压力来源
- [ ] 是否说明缓冲能力
- [ ] 是否给出后续观察点
