---
name: bondclaw-convertibles-premium-discount-watch
description: 'BondClaw 转债研究员工作流: premium-discount-watch. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — premium-discount-watch

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

围绕溢价率和折价率变化写一份跟踪笔记，判断当前估值是否偏贵或偏便宜，并说明是否适合切换风格。先给结论，再给比较，再给动作。

## 输入要求

- **date** (必填): string
- **premium_range** (必填): string
- **candidate_bonds** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- premium_range: "中等偏高"
- candidate_bonds: ["可转债A","可转债B"]

## 质量检查清单

- [ ] 是否判断估值偏离
- [ ] 是否说明风格切换
- [ ] 是否给出动作建议
