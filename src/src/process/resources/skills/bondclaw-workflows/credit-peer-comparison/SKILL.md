---
name: bondclaw-credit-peer-comparison
description: 'BondClaw 信用研究员工作流: peer-comparison. 信用主体分析，包括发行人深挖、财报复核、条款审查. 输入参数后生成标准化分析报告。'
---

# 信用研究员 — peer-comparison

## 角色说明

信用主体分析，包括发行人深挖、财报复核、条款审查

## Prompt 模板

基于输入发行人、对标名单和比较维度，生成一份同业比较报告。要求按维度比较盈利、杠杆、现金流、融资和信用利差，并给出相对优劣结论。

## 输入要求

- **issuer** (必填): string
- **peer_list** (必填): array
- **compare_dimensions** (必填): array

## 输出格式

markdown

## 示例

- issuer: "示例发行人"
- peer_list: ["同业A","同业B","同业C"]
- compare_dimensions: ["盈利","杠杆","现金流"]

## 质量检查清单

- [ ] 对标名单是否合理
- [ ] 比较维度是否完整
- [ ] 相对结论是否清楚
- [ ] 是否适合研报引用
