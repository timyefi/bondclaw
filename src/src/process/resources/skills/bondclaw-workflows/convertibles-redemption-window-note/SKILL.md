---
name: bondclaw-convertibles-redemption-window-note
description: 'BondClaw 转债研究员工作流: redemption-window-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — redemption-window-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、转债列表和赎回窗口，生成一份赎回风险观察笔记。要求包含赎回条件、正股表现、溢价和条款风险、交易对策和回避建议，全文保持研报写作风格。

## 输入要求

- **date** (必填): string
- **convertible_list** (必填): array
- **redemption_window** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- convertible_list: ["转债A","转债B"]
- redemption_window: "未来 30 个交易日"

## 质量检查清单

- [ ] 赎回窗口是否明确
- [ ] 风险提示是否充分
- [ ] 交易对策是否清晰
- [ ] 是否适合盘中快速查看
