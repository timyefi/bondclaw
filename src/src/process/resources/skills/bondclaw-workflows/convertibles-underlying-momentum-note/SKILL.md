---
name: bondclaw-convertibles-underlying-momentum-note
description: 'BondClaw 转债研究员工作流: underlying-momentum-note. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — underlying-momentum-note

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

围绕正股动量写一份转债观察，说明动量对转债弹性、估值和切换节奏的影响。先判断，再解释，再给操作提示。

## 输入要求

- **date** (必填): string
- **underlying_momentum** (必填): string
- **convertible_candidates** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- underlying_momentum: "正股动量增强"
- convertible_candidates: ["可转债A","可转债B"]

## 质量检查清单

- [ ] 是否说明正股动量
- [ ] 是否连接转债弹性
- [ ] 是否给出操作提示
