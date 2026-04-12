---
name: bondclaw-trader-preclose-checklist
description: 'BondClaw 固收交易员工作流: preclose-checklist. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — preclose-checklist

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、待处理事项和收盘窗口，生成一份收盘前检查清单。要求包含库存、成交、回执、未完成事项和盘后复核提醒，保持简洁直接。

## 输入要求

- **date** (必填): string
- **open_items** (必填): array
- **close_window** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- open_items: ["库存对账","回执确认"]
- close_window: "15:00 前"

## 质量检查清单

- [ ] 待处理事项是否完整
- [ ] 收盘窗口是否明确
- [ ] 回执检查是否覆盖
- [ ] 是否适合交易员收盘前使用
