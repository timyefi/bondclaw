# Output Contract

## 固定文件名

运行目录内固定保留以下文件名：

- `run_manifest.json`
- `chapter_records.jsonl`
- `focus_list.json`
- `final_data.json`
- `pending_updates.json`
- `analysis_report.md`
- `financial_output.xlsx`

## 导出规则

- JSON 导出优先写稳定核心字段，再附加扩展字段。
- Markdown 报告先给动态重点，再给章节速览与待固化更新。
- Excel 只消费稳定核心字段和已识别扩展字段。
- 遇到未知扩展字段时，允许忽略或降级展示，不能整体失败。

## 前向兼容

- 新版读取旧记录时，允许字段缺失。
- 旧版导出逻辑不应依赖新增扩展字段是否存在。
- 新主题第一次出现时，优先进入 `pending_updates.json`，而不是强制改历史数据。

## 兼容旧调用

如果调用方只传旧式 Excel 输出路径：

1. 仍然在运行目录生成固定文件名产物。
2. 将 `financial_output.xlsx` 复制到旧路径，保证历史调用不崩。
