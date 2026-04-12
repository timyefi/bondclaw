---
name: bondclaw-credit-peer-spread-watch
description: 'BondClaw 信用研究员工作流: peer-spread-watch. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — peer-spread-watch

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

围绕主体和同业比较写一份利差观察，说明主体的相对位置、偏离是否合理、是否存在重估机会。要求先结论，再比较，再风险提示。

## 输入要求

- **date** (必填): string
- **issuer** (必填): string
- **peer_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- issuer: "示例主体"
- peer_list: ["同业A","同业B","同业C"]

## 质量检查清单

- [ ] 是否给出相对位置
- [ ] 是否说明偏离合理性
- [ ] 是否提示重估风险
