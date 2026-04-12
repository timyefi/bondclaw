---
name: bondclaw-multi-asset-relative-shift-note
description: 'BondClaw 多资产研究员工作流: relative-shift-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — relative-shift-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、相对变化和资产桶，生成一份相对变化说明。要求写清相对优势如何变化、对配置的含义、以及需要同步观察的联动信号，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **relative_shift** (必填): string
- **asset_buckets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- relative_shift: "信用相对利率走强"
- asset_buckets: ["利率","信用","转债","权益"]

## 质量检查清单

- [ ] 相对优势是否清楚
- [ ] 配置含义是否明确
- [ ] 联动信号是否完整
- [ ] 是否适合组合讨论
