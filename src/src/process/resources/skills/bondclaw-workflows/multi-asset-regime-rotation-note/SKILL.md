---
name: bondclaw-multi-asset-regime-rotation-note
description: 'BondClaw 多资产研究员工作流: regime-rotation-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — regime-rotation-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、市场风格判断和轮动触发项，生成一份多资产轮动说明。要求覆盖股债、信用、现金和权益之间的相对变化，并给出调仓优先级、风险预算和观察节点，全文保持研报写作风格。

## 输入要求

- **date** (必填): string
- **regime_view** (必填): string
- **rotation_triggers** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- regime_view: "防守切换"
- rotation_triggers: ["利率抬升","权益波动加大","信用利差走阔"]

## 质量检查清单

- [ ] 市场风格判断是否明确
- [ ] 轮动触发条件是否具体
- [ ] 优先级是否可执行
- [ ] 是否适合周会或晨会使用
