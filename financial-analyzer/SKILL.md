---
name: financial-analyzer
description: 企业年报附注优先财务分析 skill。用于对 A 股、港股或交易商协会报告先识别财报附注，再通过关键词搜索、抽样阅读和主附注目录建立来驱动逐章分析，最终生成 chapter records、动态重点、待固化更新和统一导出产物。
---

# Financial Analyzer

本 skill 采用“经验式附注工作流 + 最小编排脚本”。

## 强制流程

1. 先识别报告类型、公司名、报告期、币种、审计意见。
2. 不直接进入全文分析，必须先定位财报附注。
3. 通过关键词搜索找附注候选：
   - `财务报表附注`
   - `合并财务报表项目注释`
   - `Notes to the Financial Statements`
4. 对命中点前后做抽样阅读，确认已经进入正式附注区间。
5. 在已确认的附注区间内建立主附注目录。
   - 只记录主附注，如 `1`、`10`、`17`、`18`
   - `(a)(b)` 等子附注并入父附注，不单独成章
6. 将附注定位结果写成 `notes_workfile`。
7. 最后调用主脚本生成固定产物。

## 正文边界

- 正文只用于元信息识别和附注定位。
- 正文不得进入 `chapter_records.jsonl`。
- 正文不得参与 `focus_list.json`、`final_data.json` 和最终结论。
- 找不到可信附注区间时直接失败，不降级全文分析。

## 脚本入口

唯一入口：

- `scripts/financial_analyzer.py`

命令行接口：

```powershell
py "C:\Users\Administrator\Desktop\项目\信用工作流\年报训练\financial-analyzer\scripts\financial_analyzer.py" `
  --md "C:\path\to\report.md" `
  --notes-workfile "C:\path\to\notes_workfile.json" `
  --run-dir "C:\path\to\run_dir"
```

## notes_workfile 契约

顶层至少包含：

- `notes_start_line`
- `notes_end_line`
- `locator_evidence`
- `notes_catalog`

`notes_catalog` 每项至少包含：

- `note_no`
- `chapter_title`
- `start_line`
- `end_line`
- `evidence`

## 稳定产物

每次成功运行必须生成：

- `run_manifest.json`
- `chapter_records.jsonl`
- `focus_list.json`
- `final_data.json`
- `pending_updates.json`
- `analysis_report.md`
- `financial_output.xlsx`

失败时只生成失败态 `run_manifest.json`。

## 进化原则

- 新格式先记录到 `pending_updates.json`，不要直接写死到主脚本。
- 记录新的附注定位关键词、编号样式、标题变体、边界现象。
- 调整产物契约时读取 `references/open_record_protocol.md` 和 `references/output_contract.md`。
