---
name: bondclaw-fund-manager-drawdown-guard
description: 'BondClaw 固收基金经理工作流: drawdown-guard. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — drawdown-guard

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

基于输入日期、回撤信号和组合动作，生成一份回撤防守提示。要求说明回撤来源、当前防守动作、是否需要减风险和后续观察信号。

## 输入要求

- **date** (必填): string
- **drawdown_signal** (必填): string
- **portfolio_actions** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- drawdown_signal: "净值波动扩大"
- portfolio_actions: ["减久期","控制信用敞口"]

## 质量检查清单

- [ ] 回撤信号是否清楚
- [ ] 防守动作是否具体
- [ ] 是否需要减风险是否说明
- [ ] 是否适合周会和风控会使用
