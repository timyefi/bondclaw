---
name: bondclaw-multi-asset-cross-asset-signal-map
description: 'BondClaw 多资产研究员工作流: cross-asset-signal-map. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — cross-asset-signal-map

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、跨资产信号摘要和资产桶，生成一份跨资产信号映射。要求写清各信号之间的先后关系、对资产配置的含义和需要继续观察的联动点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **signal_summary** (必填): array
- **asset_buckets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- signal_summary: ["权益偏强","利率横盘","信用稳定"]
- asset_buckets: ["利率","信用","转债","权益"]

## 质量检查清单

- [ ] 信号之间的先后关系是否清楚
- [ ] 配置含义是否明确
- [ ] 联动点是否完整
- [ ] 是否适合组合讨论
