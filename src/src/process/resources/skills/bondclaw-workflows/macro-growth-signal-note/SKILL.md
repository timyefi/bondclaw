---
name: bondclaw-macro-growth-signal-note
description: 'BondClaw 宏观研究员工作流: growth-signal-note. 宏观经济分析，包括资金面、政策预期、海外市场. 输入参数后生成标准化分析报告。'
---

# 宏观研究员 — growth-signal-note

## 角色说明

宏观经济分析，包括资金面、政策预期、海外市场

## Prompt 模板

围绕增长信号写一份简短跟踪，说明实体经济信号如何影响政策预期、风险偏好和债市定价。要求先结论，再拆信号，再给含义。

## 输入要求

- **date** (必填): string
- **growth_signals** (必填): array
- **market_view** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- growth_signals: ["工业数据改善","消费修复"]
- market_view: "市场对稳增长预期略有抬升"

## 质量检查清单

- [ ] 是否识别增长信号
- [ ] 是否说明政策预期变化
- [ ] 是否落到债市含义
