# 数据契约与运行态

这份文档只说明最重要的文件、目录和产物关系，让开发者知道什么该看、什么该改、什么不能碰。

## 关键产物

- `run_manifest.json`：一次运行的状态和来源记录。
- `chapter_records.jsonl`：章节级抽取与摘要记录。
- `notes_workfile.json`：附注定位和处理工作文件。
- `analysis_report_scaffold.md`：草稿报告。
- `final_data_scaffold.json`：草稿结构化结果。
- `soul_export_payload_scaffold.json`：对外交付草稿。

## 正式产物

- `financial_output.xlsx`
- `analysis_report.md`
- `final_data.json`
- `soul_export_payload.json`

## 运行态边界

- 运行态目录只放动态数据。
- 核心技能目录只放能力定义和参考文档。
- 不把运行态数据写回核心技能目录。

## 你在开发时最需要记住的事

- 草稿不是最终结论。
- 产物名称本身就是契约的一部分。
- 路径和命名尽量稳定，不要随手改。

BondClaw V1 的新增产品契约见 [bondclaw_v1_product_contracts.md](bondclaw_v1_product_contracts.md)。
其中 `ReleaseManifest` 定义了品牌覆盖、发布仓库、升级域名和功能开关的集中配置结构。
其中的执行契约现在以 Windows 原生为默认。
