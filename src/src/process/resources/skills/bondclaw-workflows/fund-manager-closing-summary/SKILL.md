---
name: bondclaw-fund-manager-closing-summary
description: 'BondClaw 固收基金经理工作流: closing-summary. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — closing-summary

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

根据当天动作生成收盘总结，说明做了什么、为什么做、还有哪些问题留到明天继续跟踪。要求简洁、能进决策日志。

## 输入要求

- **date** (必填): string
- **day_actions** (必填): array
- **open_questions** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- day_actions: ["调整久期","减仓低流动性标的"]
- open_questions: ["资金面后续变化","信用事件跟踪"]

## 质量检查清单

- [ ] 是否记录当天动作
- [ ] 是否说明决策原因
- [ ] 是否列出待跟踪问题
