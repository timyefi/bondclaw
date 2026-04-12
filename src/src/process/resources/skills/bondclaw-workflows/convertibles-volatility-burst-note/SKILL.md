---
name: bondclaw-convertibles-volatility-burst-note
description: 'BondClaw 转债研究员工作流: volatility-burst-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — volatility-burst-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、波动信号和主体名称，生成一份转债波动突发观察。要求写清波动来源、正股与转债联动、估值变化、以及盘中应对动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **volatility_signal** (必填): string
- **issuer_name** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- volatility_signal: "隐含波动率突然抬升"
- issuer_name: "样本主体"

## 质量检查清单

- [ ] 波动来源是否清楚
- [ ] 正股联动是否说明
- [ ] 估值变化是否提到
- [ ] 是否适合盘中快速查看
