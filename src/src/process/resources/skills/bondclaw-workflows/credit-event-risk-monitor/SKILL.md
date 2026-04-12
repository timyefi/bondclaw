---
name: bondclaw-credit-event-risk-monitor
description: 'BondClaw 信用研究员工作流: event-risk-monitor. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — event-risk-monitor

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入发行人、日期和事件信号，生成一份信用事件风险监测笔记。要求拆解事件内容、潜在影响、市场反馈和需要继续验证的细节，语言保持研报写作风格。

## 输入要求

- **issuer** (必填): string
- **date** (必填): string
- **event_signals** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- date: "2026-04-11"
- event_signals: ["公告变更","评级关注","舆情升温"]

## 质量检查清单

- [ ] 事件描述是否清楚
- [ ] 影响评估是否有边界
- [ ] 市场反馈是否覆盖
- [ ] 后续验证是否具体
