---
name: bondclaw-multi-asset-relative-value-scan
description: 'BondClaw 多资产研究员工作流: relative-value-scan. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — relative-value-scan

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

基于输入日期、扫描范围和相对价值关注点，生成一份相对价值扫描结果。要求列出候选、比较维度、相对优势和后续跟踪信号。

## 输入要求

- **date** (必填): string
- **scan_universe** (必填): array
- **relative_focus** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- scan_universe: ["债券A","信用B","权益C"]
- relative_focus: "收益风险比"

## 质量检查清单

- [ ] 候选是否清楚
- [ ] 比较维度是否合理
- [ ] 相对优势是否写明
- [ ] 是否适合配置和交易共用
