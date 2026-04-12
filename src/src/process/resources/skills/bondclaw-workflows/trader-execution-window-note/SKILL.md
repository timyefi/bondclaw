---
name: bondclaw-trader-execution-window-note
description: 'BondClaw 固收交易员工作流: execution-window-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — execution-window-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、执行窗口和待处理交易队列，生成一份交易执行提示。要求包含优先级、流动性判断、执行顺序、回执检查和盘后复核项，表达要简洁直接但保持研报式准确。

## 输入要求

- **date** (必填): string
- **execution_window** (必填): string
- **trade_queue** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- execution_window: "上午 9:30 - 11:00"
- trade_queue: ["债券 A","债券 B","转债 C"]

## 质量检查清单

- [ ] 执行窗口是否明确
- [ ] 优先级是否清晰
- [ ] 回执检查是否完整
- [ ] 是否便于交易员快速执行
