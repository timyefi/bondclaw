---
name: bondclaw-multi-asset-correlation-map
description: 'BondClaw 多资产研究员工作流: correlation-map. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — correlation-map

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、资产配对和相关性判断，生成一份相关性地图。要求说明哪些资产联动增强或减弱、对配置和对冲的含义，以及后续观察点。

## 输入要求

- **date** (必填): string
- **asset_pairs** (必填): array
- **correlation_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- asset_pairs: ["股债","信用-利率"]
- correlation_view: "联动增强"

## 质量检查清单

- [ ] 资产配对是否明确
- [ ] 相关性判断是否清楚
- [ ] 对配置和对冲含义是否写明
- [ ] 是否便于组合讨论
