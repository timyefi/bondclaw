---
name: bondclaw-macro-data-surprise-note
description: 'BondClaw 宏观研究员工作流: data-surprise-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — data-surprise-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕宏观数据发布写一份数据超预期或不及预期点评，说明预期差、背后结构、对政策判断和市场定价的影响。要求先结论，再证据，再交易含义。

## 输入要求

- **date** (必填): string
- **data_release** (必填): string
- **consensus_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- data_release: "通胀数据发布"
- consensus_view: "市场预期持平"

## 质量检查清单

- [ ] 是否说明预期差
- [ ] 是否分析结构性原因
- [ ] 是否落到政策与定价
