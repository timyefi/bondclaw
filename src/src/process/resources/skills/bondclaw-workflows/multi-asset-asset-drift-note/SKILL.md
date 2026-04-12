---
name: bondclaw-multi-asset-asset-drift-note
description: 'BondClaw 多资产研究员工作流: asset-drift-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — asset-drift-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、资产漂移信号和资产桶，生成一份资产漂移说明。要求写清当前偏好的微调方向、潜在切换条件、跨资产传导和风险预算，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **drift_signal** (必填): string
- **asset_buckets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- drift_signal: "权益边际走强、债券偏稳"
- asset_buckets: ["利率","信用","转债","权益"]

## 质量检查清单

- [ ] 漂移方向是否明确
- [ ] 切换条件是否具体
- [ ] 传导路径是否完整
- [ ] 是否适合组合讨论
