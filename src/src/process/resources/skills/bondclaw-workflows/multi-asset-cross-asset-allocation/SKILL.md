---
name: bondclaw-multi-asset-cross-asset-allocation
description: 'BondClaw 多资产研究员工作流: cross-asset-allocation. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — cross-asset-allocation

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于多资产观点生成配置建议，重点说明股债比价、风险预算和风格切换。先结论，再理由，再操作建议。

## 输入要求

- **date** (必填): string
- **asset_views** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- asset_views: ["权益","利率债","信用债"]

## 质量检查清单

- [ ] 是否体现跨资产比较
- [ ] 是否给出配置建议
- [ ] 是否提示风险预算
