---
name: bondclaw-fund-manager-weekly-readout
description: 'BondClaw 固收基金经理工作流: weekly-readout. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — weekly-readout

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕一周事件和组合动作写一份周度读数，说明本周哪些变化最重要、组合做了什么、下周优先盯什么。要求适合周会。

## 输入要求

- **date** (必填): string
- **weekly_events** (必填): array
- **portfolio_actions** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- weekly_events: ["资金面波动","信用事件跟踪"]
- portfolio_actions: ["缩短久期","增加流动性"]

## 质量检查清单

- [ ] 是否总结一周核心事件
- [ ] 是否写清组合动作
- [ ] 是否指出下周关注点
