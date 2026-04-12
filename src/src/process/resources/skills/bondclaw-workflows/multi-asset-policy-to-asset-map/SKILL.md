---
name: bondclaw-multi-asset-policy-to-asset-map
description: 'BondClaw 多资产研究员工作流: policy-to-asset-map. 多资产配置，包括跨资产估值、体制轮动、相关性变化. 输入参数后生成标准化分析报告。'
---

# 多资产研究员 — policy-to-asset-map

## 角色说明

多资产配置，包括跨资产估值、体制轮动、相关性变化

## Prompt 模板

把政策信号映射到多资产配置视角，说明不同资产的受益和受损方向，并给出仓位上的优先级建议。要求先结论，再映射逻辑，再配置动作。

## 输入要求

- **date** (必填): string
- **policy_signals** (必填): array
- **asset_impacts** (必填): array

## 输出格式

markdown

## 示例

- date: "2026-04-10"
- policy_signals: ["稳增长预期抬升","资金面边际宽松"]
- asset_impacts: ["利率债偏友好","权益风格轮动"]

## 质量检查清单

- [ ] 是否完成政策到资产的映射
- [ ] 是否给出优先级
- [ ] 是否提示仓位风险
