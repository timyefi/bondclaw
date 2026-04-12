---
name: bondclaw-credit-covenant-breach-watch
description: 'BondClaw 信用研究员工作流: covenant-breach-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — covenant-breach-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入日期、主体名称和契约信号，生成一份契约预警观察。要求写清可能触发的条款、对应的财务压力、事件演变路径和后续验证动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **covenant_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- covenant_signals: ["净资产约束趋紧","担保空间缩小","借新还旧压力抬升"]

## 质量检查清单

- [ ] 契约触发点是否清楚
- [ ] 压力传导是否说清
- [ ] 事件路径是否具体
- [ ] 是否适合风控共享
