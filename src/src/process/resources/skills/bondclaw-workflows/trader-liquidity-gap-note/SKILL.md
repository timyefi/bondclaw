---
name: bondclaw-trader-liquidity-gap-note
description: 'BondClaw 固收交易员工作流: liquidity-gap-note. 交易执行，包括执行记录、头寸对账、收盘检查. 输入参数后生成标准化分析报告。'
---

# 固收交易员 — liquidity-gap-note

## 角色说明

交易执行，包括执行记录、头寸对账、收盘检查

## Prompt 模板

围绕库存和流动性缺口写一份交易备忘，说明哪些头寸最难处理、哪些报价最需要优先跟进、尾盘是否需要提前做动作。输出要足够短，方便交易员直接执行。

## 输入要求

- **date** (必填): string
- **inventory_snapshot** (必填): array
- **liquidity_gaps** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- inventory_snapshot: ["利率债库存偏高","部分信用债买盘不足"]
- liquidity_gaps: ["长久期债券成交慢","低评级债券点差宽"]

## 质量检查清单

- [ ] 是否标出难处理头寸
- [ ] 是否提醒优先跟进报价
- [ ] 是否给出尾盘动作建议
