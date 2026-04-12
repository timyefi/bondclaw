---
name: bondclaw-rates-auction-preview
description: 'BondClaw 利率研究员工作流: auction-preview. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — auction-preview

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、招标列表和利率观点，生成一份招标前瞻。要求包含品种重点、市场预期、可能扰动和结果观察点，语言保持研报写作风格。

## 输入要求

- **date** (必填): string
- **auction_list** (必填): array
- **rate_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- auction_list: ["7Y 国债","10Y 国开"]
- rate_view: "中性略强"

## 质量检查清单

- [ ] 招标列表是否清楚
- [ ] 预期是否合理
- [ ] 扰动因素是否明确
- [ ] 是否适合盘前快速阅读
