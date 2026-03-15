---
name: financial-analyzer
description: 开放式企业年报财务分析 skill。用于解析 A 股/港股/交易商协会年报 Markdown 或 PDF 转换结果，按逐章研究方式生成 chapter records、动态重点、待固化更新和统一导出产物；适用于财务分析、信用分析、债务结构识别、审计意见研判与技能演化场景。
---

# Financial Analyzer

按“稳定外壳 + 扩展载荷”执行，不预设固定专题清单，也不要求每次先改死 schema。

## 核心流程

1. 识别报告类型、币种、审计意见与实体基础信息。
2. 从第一章到最后一章逐章读取并生成 `chapter_records.jsonl`。
3. 每章都输出固定核心字段：
   - `chapter_no`
   - `chapter_title`
   - `status`
   - `summary`
4. 每章都允许扩展载荷自由增长：
   - `attributes`
   - `numeric_data`
   - `findings`
   - `anomalies`
   - `evidence`
   - `extensions`
5. 全章结束后，基于证据密度和风险信号动态生成 `focus_list.json`。
6. 基于全部记录聚合 `final_data.json`、`analysis_report.md`、`financial_output.xlsx`。
7. 新主题、新字段、新规则不直接写入正式知识库，先进入 `pending_updates.json`。

## 稳定产物

每次运行必须生成以下文件：

- `run_manifest.json`
- `chapter_records.jsonl`
- `focus_list.json`
- `final_data.json`
- `pending_updates.json`
- `analysis_report.md`
- `financial_output.xlsx`

如果调用方传入的是旧式 Excel 输出路径，仍然兼容复制 Excel，但稳定外壳文件名不能变化。

## 何时读取 references

- 调整记录结构或做前向兼容判断时，读取 `references/open_record_protocol.md`
- 调整重点生成逻辑时，读取 `references/focus_generation.md`
- 修改 Markdown/Excel/JSON 导出行为时，读取 `references/output_contract.md`

## 执行约束

- Windows 下优先使用 `py`，并保持 UTF-8 编码。
- 不要一次性通读全文后直接输出最终结论；必须先形成逐章记录。
- 不要把新增发现直接固化到 `knowledge_base.json`；先记录到 `pending_updates.json`。
- 不要把主题名、指标名、章节名写成唯一合法枚举；允许通过 `extensions` 增长。

## 脚本入口

- 主入口：`scripts/financial_analyzer.py`
- 新内核：`scripts/financial_analyzer_v3.py`
- 知识治理：`scripts/knowledge_manager.py`

## 推荐调用

```powershell
py "C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\financial-analyzer\scripts\financial_analyzer.py" `
  --md "C:\path\to\report.md" `
  --run-dir "C:\path\to\run_dir"
```

兼容旧调用：

```powershell
py "C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\financial-analyzer\scripts\financial_analyzer.py" `
  --md "C:\path\to\report.md" `
  --output "C:\path\to\result.xlsx"
```
