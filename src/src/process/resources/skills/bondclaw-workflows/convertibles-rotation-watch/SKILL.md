---
name: bondclaw-convertibles-rotation-watch
description: 'BondClaw 转债研究员工作流: rotation-watch. 可转债分析，包括双低筛选、Delta敞口、Gamma波段. 输入参数后生成标准化分析报告。'
---

# 转债研究员 — rotation-watch

## 角色说明

可转债分析，包括双低筛选、Delta敞口、Gamma波段

## Prompt 模板

基于输入日期、轮动判断和候选列表，生成一份转债轮动观察。要求说明轮动逻辑、候选优先级、正股驱动和需要跟踪的信号。

## 输入要求

- **date** (必填): string
- **rotation_view** (必填): string
- **candidate_list** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-11"
- rotation_view: "风格切向进攻"
- candidate_list: ["转债A","转债B","转债C"]

## 质量检查清单

- [ ] 轮动逻辑是否明确
- [ ] 优先级是否合理
- [ ] 跟踪信号是否具体
- [ ] 是否适合晨会或盘前使用
