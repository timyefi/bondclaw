---
name: bondclaw-multi-asset-regime-allocation-note
description: 'BondClaw 多资产研究员工作流: regime-allocation-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — regime-allocation-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

根据当前市场风格写一份配置备忘，说明风险偏好、资产轮动和仓位偏向。先给配置判断，再给支撑理由，再给执行优先级。

## 输入要求

- **date** (必填): string
- **market_regime** (必填): string
- **allocation_bias** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- market_regime: "震荡偏防御"
- allocation_bias: ["利率债中性偏多","权益控制回撤"]

## 质量检查清单

- [ ] 是否识别市场风格
- [ ] 是否给出配置偏向
- [ ] 是否说明执行优先级
