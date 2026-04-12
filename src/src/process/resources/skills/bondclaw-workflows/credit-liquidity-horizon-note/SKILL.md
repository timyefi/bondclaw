---
name: bondclaw-credit-liquidity-horizon-note
description: 'BondClaw 信用研究员工作流: liquidity-horizon-note. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — liquidity-horizon-note

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入日期、主体名称和流动性视野，生成一份流动性视野说明。要求写清未来几个季度的资金安排、可见融资窗口、潜在缺口和观察重点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **liquidity_horizon** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- liquidity_horizon: "未来两个季度"

## 质量检查清单

- [ ] 资金安排是否完整
- [ ] 融资窗口是否明确
- [ ] 潜在缺口是否提到
- [ ] 是否适合风控共享
