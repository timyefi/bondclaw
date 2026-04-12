---
name: bondclaw-rates-curve-attribution
description: 'BondClaw 利率研究员工作流: curve-attribution. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-attribution

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

根据输入的收益率曲线点位和市场变化，判断曲线变陡、变平或平移的主要驱动，并给出交易含义。要求结构清晰，先结论后解释。

## 输入要求

- **date** (必填): string
- **curve_points** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- curve_points: ["1Y","3Y","5Y","10Y"]

## 质量检查清单

- [ ] 是否先给曲线判断
- [ ] 是否解释驱动因素
- [ ] 是否给出交易含义
