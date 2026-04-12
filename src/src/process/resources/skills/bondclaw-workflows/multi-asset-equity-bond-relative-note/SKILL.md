---
name: bondclaw-multi-asset-equity-bond-relative-note
description: 'BondClaw 多资产研究员工作流: equity-bond-relative-note. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — equity-bond-relative-note

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

比较权益和债券信号，判断当前更适合偏权益、偏债券还是维持平衡。要求先给偏好，再给证据，再给仓位含义。

## 输入要求

- **date** (必填): string
- **equity_signals** (必填): array
- **bond_signals** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- equity_signals: ["风格轮动加快","波动率抬升"]
- bond_signals: ["长端利率震荡","资金面平稳"]

## 质量检查清单

- [ ] 是否比较股债信号
- [ ] 是否给出偏好判断
- [ ] 是否落到仓位含义
