---
name: bondclaw-trader-inventory-scan
description: 'BondClaw 固收交易员工作流: inventory-scan. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — inventory-scan

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

基于输入日期、库存列表和扫描重点，生成一份交易库存扫描笔记。要求写清库存结构、可交易性、流动性和优先处理顺序，保持研报写作风格。

## 输入要求

- **date** (必填): string
- **inventory_list** (必填): array
- **scan_focus** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- inventory_list: ["债券A","债券B","转债C"]
- scan_focus: "流动性与久期"

## 质量检查清单

- [ ] 库存列表是否完整
- [ ] 交易性判断是否清楚
- [ ] 优先顺序是否明确
- [ ] 是否适合交易员盘前使用
