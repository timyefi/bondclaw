---
name: bondclaw-credit-issuer-liquidity-watch
description: 'BondClaw 信用研究员工作流: issuer-liquidity-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — issuer-liquidity-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入日期、主体名称和流动性信号，生成一份主体流动性跟踪。要求写清现金来源、融资可得性、潜在压力点和需要继续观察的融资节点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **issuer_name** (必填): string
- **liquidity_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- issuer_name: "样本主体"
- liquidity_signals: ["授信收缩","回款放缓","再融资窗口变窄"]

## 质量检查清单

- [ ] 现金和融资路径是否清楚
- [ ] 压力点是否具体
- [ ] 后续观察节点是否明确
- [ ] 是否适合风控与研究共享
