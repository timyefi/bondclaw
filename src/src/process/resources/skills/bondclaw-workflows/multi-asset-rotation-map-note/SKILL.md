---
name: bondclaw-multi-asset-rotation-map-note
description: 'BondClaw 多资产研究员工作流: rotation-map-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — rotation-map-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、风格轮动信号和资产桶，生成一份轮动映射说明。要求写清当前偏好、回避项、跨资产传导路径和需要保留的风险预算，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **rotation_signal** (必填): string
- **asset_buckets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- rotation_signal: "风格从防御切向进攻"
- asset_buckets: ["利率","信用","转债","权益"]

## 质量检查清单

- [ ] 轮动方向是否明确
- [ ] 资产偏好是否可执行
- [ ] 传导路径是否说清
- [ ] 是否适合组合讨论
