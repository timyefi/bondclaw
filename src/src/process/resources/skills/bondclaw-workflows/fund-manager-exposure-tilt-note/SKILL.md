---
name: bondclaw-fund-manager-exposure-tilt-note
description: 'BondClaw 固收基金经理工作流: exposure-tilt-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — exposure-tilt-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、敞口状态和倾斜信号，生成一份敞口倾斜说明。要求写清当前敞口偏向、为何倾斜、需要保留的约束以及下一步验证点，全文使用研报写作风格。

## 输入要求

- **date** (必填): string
- **exposure_state** (必填): string
- **tilt_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- exposure_state: "久期略高、信用中性"
- tilt_signals: ["利率波动收敛","信用利差稳定"]

## 质量检查清单

- [ ] 敞口偏向是否清楚
- [ ] 倾斜理由是否明确
- [ ] 约束是否保留
- [ ] 是否适合投委或晨会使用
