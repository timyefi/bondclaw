---
name: bondclaw-rates-auction-aftertaste-note
description: 'BondClaw 利率研究员工作流: auction-aftertaste-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — auction-aftertaste-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

围绕招标后的市场反应写一份余味点评，说明结果是否改变了市场对供给和定价的判断。要求先给结论，再给结果，再给含义。

## 输入要求

- **date** (必填): string
- **auction_result** (必填): string
- **price_action** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- auction_result: "结果偏稳"
- price_action: ["中长端跟随","短端波动有限"]

## 质量检查清单

- [ ] 是否说明招标结果
- [ ] 是否分析市场反应
- [ ] 是否给出含义
