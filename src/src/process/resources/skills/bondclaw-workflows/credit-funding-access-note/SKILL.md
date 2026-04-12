---
name: bondclaw-credit-funding-access-note
description: 'BondClaw 信用研究员工作流: funding-access-note. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — funding-access-note

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

针对输入发行人和融资信号，生成一份融资可得性观察笔记。要求拆解银行授信、债券融资、非标替代和再融资路径，并给出对信用利差和持仓策略的含义，全文保持研报写作风格。

## 输入要求

- **issuer** (必填): string
- **date** (必填): string
- **funding_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- date: "2026-04-11"
- funding_signals: ["授信收紧","债券发行推迟","融资成本抬升"]

## 质量检查清单

- [ ] 融资信号是否具体
- [ ] 路径拆解是否完整
- [ ] 对利差和持仓含义是否明确
- [ ] 是否适合作为信用晨会材料
