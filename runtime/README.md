# Runtime 目录说明

本目录是项目内可携带的 production runtime 根目录。

当前阶段结论：

- `runtime_config + knowledge_base + adoption_logs` 目录骨架进入 Git。
- `registry / batches / governance_review / logs / tmp` 属于运行态状态目录，不应作为日常版本化资产管理。
- 运行中的动态数据不得写入 `~/.codex/skills`。
- 逐份报告独立闭环入口由 `financial-analyzer/scripts/run_report_series.py` 承担；它复用同一套下载、解析、单案分析和 registry 更新逻辑，默认只停在 scaffold，正式报告与 Excel 需要显式 formalize 后再产出，不在同一结果里合并多份报告。
- 如果已经有 19 份正式产物，`financial-analyzer/scripts/run_vanke_longitudinal_study.py --postformalize-only --formalize` 会直接读取既有正式输出并生成阅读 ledger 与 workbook，不会重跑下载或 MinerU 解析；正式 `analysis_report.md` 需要 Codex 再根据这些阅读材料单独写作。

当前 P1 只落规范与静态基线：

- 不修改脚本默认路径
- 不实现 registry 逻辑
- 不启动 10 案测试

正式规范见：

- [runtime_external_data_layer_spec.md](/Users/yetim/project/financialanalysis/runtime_external_data_layer_spec.md)
