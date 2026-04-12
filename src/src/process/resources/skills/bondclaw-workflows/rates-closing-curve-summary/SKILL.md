---
name: bondclaw-rates-closing-curve-summary
description: 'BondClaw 利率研究员工作流: closing-curve-summary. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — closing-curve-summary

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

根据收盘时点的曲线变化生成简短总结，说明当天曲线如何演绎、哪些期限最值得关注、明天需要盯什么。先给结论，再给曲线变化，再给后续关注。

## 输入要求

- **date** (必填): string
- **curve_moves** (必填): array
- **end_of_day_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- curve_moves: ["5Y收益率下行","10Y波动收窄"]
- end_of_day_view: "长端支撑仍在"

## 质量检查清单

- [ ] 是否总结曲线变化
- [ ] 是否指出关注期限
- [ ] 是否说明次日跟踪
