---
name: financialanalysis
description: "BondClaw 固收财务分析核心技能。从官方来源采集财报（ChinaMoney），解析 PDF（MinerU），执行附注优先分析（Financial Analyzer）。触发词：'财报分析', '信用分析', '附注分析', '年报解析', '财务分析', 'PDF 解析', '中国货币网'。"
---

# BondClaw 财务分析技能

## 概览

本技能是 BondClaw 的分析核心，由三个子技能组成：

1. **ChinaMoney** — 从中国货币网等官方来源下载财报和披露材料
2. **MinerU** — 将 PDF、Word、PPT、图片转成 Markdown 或结构化中间文本
3. **Financial Analyzer** — 按附注优先原则生成分析底稿、报告草稿和结构化结果

## 工作流

```
任务定义(issuer-year)
  → 数据采集层（ChinaMoney）
  → 文档理解层（MinerU）
  → 文档标准化层（定位主体、期间、附注范围）
  → 分析引擎层（Financial Analyzer）
```

## 子技能

### ChinaMoney

路径：`skills/financialanalysis/chinamoney/`
从中国货币网下载年报、公告和披露文件。

### MinerU

路径：`skills/financialanalysis/mineru/`
PDF 文档解析，支持财报、公告等文档的结构化转换。

### Financial Analyzer

路径：`skills/financialanalysis/financial-analyzer/`
附注优先分析引擎，生成标准化工作底稿和分析报告。

## 使用场景

- 对债券发行主体进行信用分析
- 从 PDF 年报中提取财务数据和附注信息
- 生成标准化的财务分析工作底稿
- 按附注优先原则组织分析流程
