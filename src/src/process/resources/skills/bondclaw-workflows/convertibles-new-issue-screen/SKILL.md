---
name: bondclaw-convertibles-new-issue-screen
description: 'BondClaw 转债研究员工作流: new-issue-screen. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — new-issue-screen

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入发行列表和筛选标准，输出一份转债新券筛选结果。要求列出筛选逻辑、候选排序、关键条款、正股观察点和交易提醒，写作风格保持研报化。

## 输入要求

- **date** (必填): string
- **issue_list** (必填): array
- **screen_criteria** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- issue_list: ["新券A","新券B","新券C"]
- screen_criteria: "双低、条款友好、正股弹性"

## 质量检查清单

- [ ] 筛选标准是否清楚
- [ ] 候选排序是否合理
- [ ] 条款和正股是否都覆盖
- [ ] 是否适合盘前直接使用
