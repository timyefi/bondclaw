---
name: bondclaw-rates-curve-shape-update
description: 'BondClaw 利率研究员工作流: curve-shape-update. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-shape-update

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

基于输入日期、曲线形态和驱动摘要，生成一份曲线形态更新。要求说明陡峭化/平坦化/熊陡/牛平等变化、驱动因素、交易影响和风险提示。

## 输入要求

- **date** (必填): string
- **curve_shape** (必填): string
- **driver_summary** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- curve_shape: "平坦化"
- driver_summary: ["资金偏紧","招标偏弱"]

## 质量检查清单

- [ ] 曲线形态是否准确
- [ ] 驱动因素是否完整
- [ ] 交易影响是否说明
- [ ] 是否适合交易员和研究员共用
