---
name: bondclaw-convertibles-terms-alert
description: 'BondClaw 转债研究员工作流: terms-alert. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — terms-alert

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、条款更新和转债列表，生成一份条款提醒。要求说明条款变化、潜在影响、对应标的和是否需要立刻调整关注顺序。

## 输入要求

- **date** (必填): string
- **terms_updates** (必填): array
- **convertible_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- terms_updates: ["回售条件变化","赎回窗口变化"]
- convertible_list: ["转债A","转债B"]

## 质量检查清单

- [ ] 条款变化是否写明
- [ ] 影响标的是否清楚
- [ ] 是否需要调整关注顺序
- [ ] 是否适合交易员和研究员共用
