---
name: bondclaw-rates-auction-allocation-note
description: 'BondClaw 利率研究员工作流: auction-allocation-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — auction-allocation-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

根据招标和认购结果写一份分配点评，说明中标情况、需求强弱、结果对曲线和利差的含义。要求结论前置、结构清楚。

## 输入要求

- **date** (必填): string
- **auction_details** (必填): array
- **market_color** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- auction_details: ["7Y国债发行","边际认购偏强"]
- market_color: "中长端需求平稳"

## 质量检查清单

- [ ] 是否说明中标和分配含义
- [ ] 是否判断需求强弱
- [ ] 是否落到曲线和利差
