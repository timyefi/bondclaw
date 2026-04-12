---
name: bondclaw-multi-asset-allocation-shift-note
description: 'BondClaw 多资产研究员工作流: allocation-shift-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — allocation-shift-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、配置变化和资产桶，生成一份配置变化说明。要求写清从哪里减、往哪里加、背后的因子和需要保留的风险预算，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **allocation_shift** (必填): string
- **asset_buckets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- allocation_shift: "利率减仓、信用加仓"
- asset_buckets: ["利率","信用","转债","权益"]

## 质量检查清单

- [ ] 调整方向是否清楚
- [ ] 因子是否完整
- [ ] 风险预算是否保留
- [ ] 是否适合组合讨论
