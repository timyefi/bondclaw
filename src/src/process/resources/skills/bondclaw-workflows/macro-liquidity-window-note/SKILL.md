---
name: bondclaw-macro-liquidity-window-note
description: 'BondClaw 宏观研究员工作流: liquidity-window-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — liquidity-window-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、资金信号和关注主题，生成一份流动性窗口观察笔记。要求先给结论，再给资金面变化、政策背景、对利率和信用的传导、风险提示，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **liquidity_signal** (必填): string
- **focus_topics** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- liquidity_signal: "隔夜与 7D 资金波动"
- focus_topics: ["资金面","利率","信用"]

## 质量检查清单

- [ ] 资金信号是否写清
- [ ] 传导路径是否明确
- [ ] 风险提示是否到位
- [ ] 是否适合晨会快速阅读
