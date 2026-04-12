---
name: bondclaw-macro-macro-scenario-update
description: 'BondClaw 宏观研究员工作流: macro-scenario-update. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — macro-scenario-update

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

基于输入日期、场景标题和场景变化，生成一份宏观场景更新。要求先给核心判断，再给变化点、驱动因素、对利率和信用的含义，以及需要修正的观察假设。

## 输入要求

- **date** (必填): string
- **scenario_title** (必填): string
- **scenario_change** (必填): string
- **focus_topics** (可选): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- scenario_title: "宽松预期回摆"
- scenario_change: "政策表述边际收紧"
- focus_topics: ["政策预期","资金面"]

## 质量检查清单

- [ ] 场景判断是否明确
- [ ] 变化点是否具体
- [ ] 含义是否覆盖利率和信用
- [ ] 是否便于内部复盘
