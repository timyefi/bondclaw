---
name: bondclaw-convertibles-flow-watch-note
description: 'BondClaw 转债研究员工作流: flow-watch-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — flow-watch-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、资金流信号和主体名称，生成一份转债资金流观察。要求写清是主动流入还是流出、对估值和波动的影响、以及盘中最需要观察的动作，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **flow_signal** (必填): string
- **issuer_name** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- flow_signal: "资金明显流入"
- issuer_name: "样本主体"

## 质量检查清单

- [ ] 资金流方向是否明确
- [ ] 估值和波动影响是否提到
- [ ] 盘中动作是否具体
- [ ] 是否适合快速查看
