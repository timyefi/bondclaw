---
name: bondclaw-credit-refinancing-track
description: 'BondClaw 信用研究员工作流: refinancing-track. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — refinancing-track

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入发行人、日期和再融资信号，生成一份再融资跟踪笔记。要求说明资金缺口、替代融资、期限安排和利差影响，并给出下一步验证点。

## 输入要求

- **issuer** (必填): string
- **date** (必填): string
- **refinancing_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- date: "2026-04-11"
- refinancing_signals: ["短债压力","银行授信波动","债券发行计划变化"]

## 质量检查清单

- [ ] 再融资信号是否明确
- [ ] 期限安排是否写清
- [ ] 利差影响是否说明
- [ ] 验证点是否具体
