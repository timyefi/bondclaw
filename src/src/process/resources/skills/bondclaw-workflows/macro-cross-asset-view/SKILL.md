---
name: bondclaw-macro-cross-asset-view
description: 'BondClaw 宏观研究员工作流: cross-asset-view. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — cross-asset-view

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、资产类别和宏观主题，输出一份跨资产联动观察。要求把债券、权益、商品和外汇的方向一起看，说明宏观主题如何传导，并给出固收资产的操作含义。

## 输入要求

- **date** (必填): string
- **asset_classes** (必填): array
- **macro_theme** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- asset_classes: ["债券","权益","外汇"]
- macro_theme: "增长预期变化"

## 质量检查清单

- [ ] 资产联动是否覆盖
- [ ] 传导逻辑是否清楚
- [ ] 固收含义是否明确
- [ ] 是否便于投研团队共享
