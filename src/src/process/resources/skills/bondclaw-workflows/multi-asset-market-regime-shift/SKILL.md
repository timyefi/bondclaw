---
name: bondclaw-multi-asset-market-regime-shift
description: 'BondClaw 多资产研究员工作流: market-regime-shift. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — market-regime-shift

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、市场风格变化和关注资产，生成一份市场风格切换观察。要求写清风格变化、触发因素、资产影响和配置建议。

## 输入要求

- **date** (必填): string
- **regime_change** (必填): string
- **focus_assets** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- regime_change: "风险偏好回落"
- focus_assets: ["债券","信用","权益"]

## 质量检查清单

- [ ] 风格变化是否清楚
- [ ] 触发因素是否具体
- [ ] 资产影响是否覆盖
- [ ] 是否便于快速决策
