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

- `analysis_report.md`
- `final_data.json`
- `soul_export_payload.json`
- `financial_output.xlsx`

## 导出规则

- 模板脚本输出的 scaffold 只能视为草稿，不能未经复核直接作为最终交付。
- 主链路默认停在 scaffold；正式 `analysis_report.md` 和 `financial_output.xlsx` 需要在 Codex 读完中间产物后显式 formalize。
- `soul_export_payload.json` 仍是 Soul Excel 导出层的正式稳定契约。
- `financial_output.xlsx` 由独立 Soul exporter 基于正式 `soul_export_payload.json` 生成。
- Excel 只消费稳定核心字段和已确认结构，不消费内部知识治理元数据。
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
