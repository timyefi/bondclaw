---
name: bondclaw-credit-repayment-calendar-watch
description: 'BondClaw 信用研究员工作流: repayment-calendar-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — repayment-calendar-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕偿债日历写一份跟踪笔记，说明未来一段时间的到期压力、再融资风险和需要提前警惕的节点。要求先结论，再列日历，再给风险。

## 输入要求

- **date** (必填): string
- **repayment_calendar** (必填): array
- **refinancing_risks** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- repayment_calendar: ["5月到期短债","6月回售窗口"]
- refinancing_risks: ["融资收缩","展期预期上升"]

## 质量检查清单

- [ ] 是否列出到期节点
- [ ] 是否说明再融资风险
- [ ] 是否给出预警判断
