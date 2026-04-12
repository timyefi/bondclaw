---
name: bondclaw-fund-manager-daily-position-note
description: 'BondClaw 固收基金经理工作流: daily-position-note. 组合管理，包括晨会打包、风险审查、策略更新. 输入参数后生成标准化分析报告。'
---

# 固收基金经理 — daily-position-note

## 角色说明

组合管理，包括晨会打包、风险审查、策略更新

## Prompt 模板

围绕当日持仓生成一份简短仓位说明，说明当前配置、夜盘变化、需要重点关注的风险和今天要盯的动作。要求简洁、适合日常晨会后使用。

## 输入要求

- **date** (必填): string
- **position_summary** (必填): array
- **overnight_changes** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- position_summary: ["久期中性","信用偏中高等级"]
- overnight_changes: ["海外利率波动","存单收益率变化"]

## 质量检查清单

- [ ] 是否说明当前配置
- [ ] 是否覆盖夜盘变化
- [ ] 是否有今日关注动作
