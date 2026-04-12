---
name: bondclaw-rates-curve-positioning-note
description: 'BondClaw 利率研究员工作流: curve-positioning-note. 利率曲线分析，包括期限利差、招投标、曲线定位. 输入参数后生成标准化分析报告。'
---

# 利率研究员 — curve-positioning-note

## 角色说明

利率曲线分析，包括期限利差、招投标、曲线定位

## Prompt 模板

围绕收益率曲线位置写一份交易定位说明，判断当前适合做陡峭化、平坦化还是维持中性久期。先给判断，再给证据，再给执行建议。

## 输入要求

- **date** (必填): string
- **curve_view** (必填): string
- **positioning_bias** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- curve_view: "中段偏贵，长端支撑尚在"
- positioning_bias: ["适度防守","关注曲线变陡"]

## 质量检查清单

- [ ] 是否给出曲线定位
- [ ] 是否说明偏向
- [ ] 是否给出执行建议
