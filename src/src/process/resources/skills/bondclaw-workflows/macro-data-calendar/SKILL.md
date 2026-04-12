---
name: bondclaw-macro-data-calendar
description: 'BondClaw 宏观研究员工作流: data-calendar. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — data-calendar

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期和数据点，生成一份宏观数据日历。要求按照时间顺序列出数据名称、预期关注点、可能影响的资产方向和需要提前准备的问题，保持研报写作风格。

## 输入要求

- **calendar_date** (必填): string
- **data_points** (必填): array

## 输出格式

markdown

## 示例

- calendar_date: "2026-04-11"
- data_points: ["社融","通胀","进出口"]

## 质量检查清单

- [ ] 数据点是否完整
- [ ] 时间顺序是否清楚
- [ ] 资产影响是否写明
- [ ] 是否适合盘前查看
