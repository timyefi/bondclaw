---
name: bondclaw-macro-funding-condition-watch
description: 'BondClaw 宏观研究员工作流: funding-condition-watch. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — funding-condition-watch

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕资金面和政策预期写一份观察笔记，说明资金松紧、公开市场操作、同业存单和机构行为的联动。先给判断，再给数据，再给对债市的含义。

## 输入要求

- **date** (必填): string
- **money_market_signals** (必填): array
- **policy_expectation** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- money_market_signals: ["DR007维持稳定","同业存单发行节奏加快"]
- policy_expectation: "稳资金预期延续"

## 质量检查清单

- [ ] 是否讲清资金松紧
- [ ] 是否说明政策与市场的联动
- [ ] 是否给出债市含义
