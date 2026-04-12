---
name: bondclaw-trader-position-reconciliation-note
description: 'BondClaw 固收交易员工作流: position-reconciliation-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — position-reconciliation-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

围绕头寸对账写一份简短跟进，说明库存、成交、回执和系统记录之间是否一致。要求明确、简短、便于收盘后跟进。

## 输入要求

- **date** (必填): string
- **position_book** (必填): array
- **reconciliation_items** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- position_book: ["利率债久期持仓","信用债分散持仓"]
- reconciliation_items: ["系统记录核对","成交回执核对"]

## 质量检查清单

- [ ] 是否覆盖头寸与成交核对
- [ ] 是否列出对账事项
- [ ] 是否便于收盘后处理
