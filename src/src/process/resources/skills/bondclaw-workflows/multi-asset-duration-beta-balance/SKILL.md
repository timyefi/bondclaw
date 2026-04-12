---
name: bondclaw-multi-asset-duration-beta-balance
description: 'BondClaw 多资产研究员工作流: duration-beta-balance. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — duration-beta-balance

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

围绕久期和 beta 的平衡写一份配置说明，判断当前组合更适合提高防御性还是维持弹性。先给判断，再给原因，再给动作。

## 输入要求

- **date** (必填): string
- **duration_view** (必填): string
- **beta_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- duration_view: "久期中性偏长"
- beta_view: "权益 beta 略高"

## 质量检查清单

- [ ] 是否讨论久期与 beta
- [ ] 是否给出防御性判断
- [ ] 是否能转化为动作
