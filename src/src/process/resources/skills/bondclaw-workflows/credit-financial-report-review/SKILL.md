---
name: bondclaw-credit-financial-report-review
description: 'BondClaw 信用研究员工作流: financial-report-review. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — financial-report-review

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入发行人、报告期和关注指标，生成一份财报解读。要求先给信用结论，再给利润、现金流、负债和非经常性项目的分析，最后给后续跟踪建议。

## 输入要求

- **issuer** (必填): string
- **report_period** (必填): string
- **focus_metrics** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- report_period: "2025 年年报"
- focus_metrics: ["营业收入","经营现金流","有息负债"]

## 质量检查清单

- [ ] 信用结论是否先行
- [ ] 财务指标是否解释到位
- [ ] 现金流和负债是否覆盖
- [ ] 是否适合基金经理快速阅读
