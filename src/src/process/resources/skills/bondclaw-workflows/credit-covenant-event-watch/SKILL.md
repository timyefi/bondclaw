---
name: bondclaw-credit-covenant-event-watch
description: 'BondClaw 信用研究员工作流: covenant-event-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — covenant-event-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕主体条款事件和风险信号写一份监控简报，强调条款触发、保护边界、可能的违约路径和需要追踪的变量。输出适合内部预警。

## 输入要求

- **issuer** (必填): string
- **covenant_events** (必填): array
- **early_warning_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例主体"
- covenant_events: ["担保结构变化","新增限制性条款"]
- early_warning_signals: ["外部融资收紧","经营现金流波动"]

## 质量检查清单

- [ ] 是否明确条款事件
- [ ] 是否识别预警信号
- [ ] 是否说明可能路径
