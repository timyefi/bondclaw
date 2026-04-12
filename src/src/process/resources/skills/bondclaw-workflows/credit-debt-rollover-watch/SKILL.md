---
name: bondclaw-credit-debt-rollover-watch
description: 'BondClaw 信用研究员工作流: debt-rollover-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — debt-rollover-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入日期、主体名称和到期滚动信号，生成一份债务滚动观察。要求写清到期压力、滚动可得性、替代融资路径和需要继续跟踪的节点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **rollover_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- rollover_signals: ["短债集中到期","银行授信收紧","再融资条件不稳"]

## 质量检查清单

- [ ] 到期压力是否清楚
- [ ] 滚动路径是否明确
- [ ] 替代融资路径是否提到
- [ ] 是否适合风控和研究共享
