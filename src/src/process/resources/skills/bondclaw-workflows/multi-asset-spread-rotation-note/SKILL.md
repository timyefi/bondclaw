---
name: bondclaw-multi-asset-spread-rotation-note
description: 'BondClaw 多资产研究员工作流: spread-rotation-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — spread-rotation-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

围绕利差变化写一份轮动提示，说明不同资产间的相对便宜与相对昂贵如何影响配置顺序。先结论，再说明利差，再给轮动方向。

## 输入要求

- **date** (必填): string
- **spread_signals** (必填): array
- **rotation_bias** (必填): string

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- spread_signals: ["股债利差收窄","信用利差分化"]
- rotation_bias: "偏防御"

## 质量检查清单

- [ ] 是否识别利差信号
- [ ] 是否给出轮动方向
- [ ] 是否说明配置顺序
