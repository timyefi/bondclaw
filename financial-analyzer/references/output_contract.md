# Output Contract

## 模板脚本固定文件名

模板脚本成功态在运行目录内固定保留以下文件名：

- `run_manifest.json`
- `chapter_records.jsonl`
- `analysis_report_scaffold.md`
- `focus_list_scaffold.json`
- `final_data_scaffold.json`
- `soul_export_payload_scaffold.json`

## Codex 复核后的正式文件名

完成逐章复核和最终汇总后，运行目录内正式交付文件名为：

- `financial_output.xlsx`
- `analysis_report.md`
- `final_data.json`
- `soul_export_payload.json`

## 导出规则

- 模板脚本输出的 scaffold 只能视为草稿，不能未经复核直接作为最终交付。
- 主链路默认停在 scaffold；正式 `financial_output.xlsx` 需要在 Codex 完成标准化 workpaper 后显式 formalize，正式 `analysis_report.md` 只能建立在该 workpaper 之上。
- `financial_output.xlsx` 是客户可展示的正式底稿，不是报告的附属摘要。
- `soul_export_payload.json` 仍是结构化中间契约，供底稿与报告共享稳定字段，但不替代 workpaper 本身。
- Excel 只消费稳定核心字段和已确认结构，不消费内部知识治理元数据。
- 如需版式收尾，可再用 `spreadsheet` 做格式微调，但不能改动底稿口径。
- 所有正常分析产物都只基于附注章节生成。

## 前向兼容

- 新版读取旧记录时，允许字段缺失。
- 旧版逻辑看到 scaffold 文件时，不应将其误认为正式分析完成。
- 不再要求主链路生成 `pending_updates.json`。

## 失败契约

如果缺少 `notes_workfile`、附注目录为空、边界无效：

1. 脚本非零退出。
2. `run_manifest.json` 中必须带 `failure_reason`。
3. 对于前置输入失败，可只生成失败态 `run_manifest.json`。
4. 失败时不得写成功态 scaffold 或正式交付文件。
