---
name: bondclaw-multi-asset-rebalancing-note
description: 'BondClaw 多资产研究员工作流: rebalancing-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — rebalancing-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入组合观点和再平衡触发项，生成一份多资产再平衡说明。要求覆盖股债、信用、现金和权益之间的配置变化，并给出风险预算与执行优先级，全文保持研报写作风格。

## 输入要求

- **date** (必填): string
- **portfolio_view** (必填): string
- **rebalance_triggers** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- portfolio_view: "防守偏多"
- rebalance_triggers: ["利率上行","权益波动放大","信用利差走阔"]

## 质量检查清单

- [ ] 组合观点是否清晰
- [ ] 再平衡触发条件是否具体
- [ ] 资产之间的联动是否写明
- [ ] 是否可以直接给基金经理参考
