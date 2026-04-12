---
name: bondclaw-rates-liquidity-gap-watch
description: 'BondClaw 利率研究员工作流: liquidity-gap-watch. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — liquidity-gap-watch

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

围绕资金缺口和期限分层写一份观察笔记，说明短端与中长端之间的资金传导是否出现断点，以及对应的交易含义。输出要短而完整。

## 输入要求

- **date** (必填): string
- **funding_readings** (必填): array
- **gap_observations** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- funding_readings: ["DR007平稳","存单利率小幅上行"]
- gap_observations: ["1Y与5Y分化","长端买盘延续"]

## 质量检查清单

- [ ] 是否说明资金传导
- [ ] 是否识别期限分层
- [ ] 是否给出交易含义
