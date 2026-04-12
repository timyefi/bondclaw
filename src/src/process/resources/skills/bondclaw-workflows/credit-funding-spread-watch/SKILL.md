---
name: bondclaw-credit-funding-spread-watch
description: 'BondClaw 信用研究员工作流: funding-spread-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — funding-spread-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入日期、主体名称和融资利差信号，生成一份融资利差观察。要求写清融资成本变化、可替代融资路径、和需要继续跟踪的市场窗口，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **funding_spreads** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- funding_spreads: ["银行贷款上浮","债券发行利差抬升"]

## 质量检查清单

- [ ] 成本变化是否说清
- [ ] 替代融资路径是否明确
- [ ] 市场窗口是否提到
- [ ] 是否适合风控共享
