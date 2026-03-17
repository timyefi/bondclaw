# Processed Reports Registry 规范（P2）

## 1. 文档定位

本文档是生产化阶段 P2 的正式规范，定义：

1. 全局已处理财报 registry 的正式 schema。
2. 财报唯一标识、文档指纹、处理指纹的生成规则。
3. 去重规则、默认重跑规则与历史回填规则。
4. `batch_manifest.json`、`task_results.jsonl` 与 registry 的关系。

正式落点固定为：

- [runtime/state/registry/processed_reports/processed_reports.json](/Users/yetim/project/financialanalysis/runtime/state/registry/processed_reports/processed_reports.json)

P2 继续遵守 P1 口径：

- registry 属于运行态状态数据，不进入 Git。
- registry 不得写入 `~/.codex/skills`。

## 2. 设计目标

- 支持跨批次、跨历史追踪同一份财报是否已经处理过。
- 区分“同一份报告”“同一份文档版本”“同一轮处理配置”。
- 在不改任务清单格式的前提下，为现有 W7 batch runner 增加全局去重与重跑判定。
- 回填已有 W6/W7 历史产物，避免 registry 从零开始失忆。

## 3. 核心模型

### 3.1 三层标识

P2 采用三层标识：

1. `report_key`
   - 业务级财报身份。
   - 表示“哪一家、哪一年、哪种报告类型”的同一份报告。
2. `document_fingerprint`
   - 具体 Markdown 文档版本身份。
   - 表示“这一份报告当前对应的文档内容版本”。
3. `processing_fingerprint`
   - 具体处理身份。
   - 表示“同一份文档在某个 engine 版本和某个 notes_workfile 内容下的一次处理配置”。

### 3.2 唯一标识规则

`report_key` 计算规则：

```text
report_key = sha256(normalized_company_name + "|" + report_period + "|" + report_type)
```

其中：

- `normalized_company_name` = 公司名去空白、转小写、去常见标点后的结果
- `report_period` = 例如 `2024`
- `report_type` = 例如 `hong_kong_full_report`

`document_fingerprint` 计算规则：

```text
document_fingerprint = "md5:<manifest.input.md5>|size:<manifest.input.file_size>"
```

`processing_fingerprint` 计算规则：

```text
processing_fingerprint = sha256(
  report_key + "|" +
  document_fingerprint + "|" +
  engine_version + "|" +
  notes_workfile_fingerprint_or_missing_marker
)
```

`notes_workfile_fingerprint` 规则：

- 文件存在时：`sha256:<file_sha256>`
- 文件不存在时：`missing:<resolved_abs_path>`

### 3.3 身份口径

当前 P2 默认：

- 同一 Markdown 文档对应同一份财报身份，只要 `company_name + report_period + report_type` 不变，就仍是同一 `report_key`
- `notes_workfile` 变化不拆成新报告，只作为同一报告的不同处理尝试
- 文档内容变化会产生新的 `document_fingerprint`

## 4. Schema

顶层结构固定为：

```json
{
  "schema_version": "processed_reports_registry_v1",
  "generated_at": "2026-03-17T12:00:00+08:00",
  "updated_at": "2026-03-17T12:05:00+08:00",
  "stats": {
    "report_count": 0,
    "document_version_count": 0,
    "attempt_count": 0,
    "success_attempt_count": 0,
    "failed_attempt_count": 0,
    "needs_rerun_count": 0
  },
  "reports": {}
}
```

`reports[report_key]` 结构固定包含：

- `identity`
  - `company_name`
  - `normalized_company_name`
  - `report_period`
  - `report_type`
- `aliases`
  - `issuer_names`
  - `task_ids`
  - `source_pdfs`
- `document_versions`
- `attempts`
- `latest_attempt_id`
- `latest_success_attempt_id`
- `processing_state`

### 4.1 `document_versions`

`document_versions` 以 `document_fingerprint` 为键，记录：

- `document_fingerprint`
- `md5`
- `file_size`
- `sample_md_path`
- `first_seen_at`
- `last_seen_at`
- `latest_attempt_id`
- `latest_success_attempt_id`
- `success_count`
- `failed_count`

### 4.2 `attempts`

每条 `attempt` 必须包含：

- `attempt_id`
- `processed_at`
- `status`
- `failure_reason`
- `engine_version`
- `knowledge_base_version`
- `document_fingerprint`
- `processing_fingerprint`
- `notes_locator_status`
- `notes_workfile`
  - `path`
  - `fingerprint`
- `artifacts`
- `source_ref`

### 4.3 `source_ref`

`source_ref` 固定包含：

- `source_kind`
  - `batch_task` 或 `legacy_single_run`
- `batch_name`
- `batch_run_dir`
- `batch_manifest_path`
- `task_results_path`
- `task_id`
- `run_dir`
- `manifest_path`
- `completed_at`

### 4.4 `processing_state`

`processing_state` 用于 registry 内的当前高层判断，固定包含：

- `latest_status`
- `latest_processed_at`
- `latest_engine_version`
- `latest_document_fingerprint`
- `latest_success_engine_version`
- `latest_success_document_fingerprint`
- `needs_rerun`
- `rerun_reasons`
- `audit_flags`

## 5. 去重规则

### 5.1 attempt 级去重

以下情况视为同一次历史 attempt，重复写入时忽略：

- 同一 `report_key`
- 同一 `processing_fingerprint`
- 同一 `manifest_path`
- 同一 `run_dir`

这条规则主要用于：

- 首次回填后再次回填同一目录
- 同一批次恢复写入时避免重复插入同一 manifest

### 5.2 报告级去重

以下情况不新建报告条目，只追加历史：

- 同一 `report_key`
- 同一 `document_fingerprint`
- 但不同批次、不同 `task_id`、不同 `run_dir`

这代表：

- 仍是同一份报告、同一版文档
- 只是发生了新的处理尝试或出现在新的批次

### 5.3 文档版本新增

以下情况仍归属于同一 `report_key`，但新增一个 `document_versions[document_fingerprint]`：

- 同一 `report_key`
- 不同 `document_fingerprint`

这代表：

- 仍是同一份业务报告
- 但 Markdown 文档内容发生了变化

### 5.4 notes_workfile 变化

`notes_workfile` 变化：

- 不新建 `report_key`
- 不新建业务报告
- 只改变 `processing_fingerprint`
- 作为同一报告的不同处理尝试保留在 `attempts`
- 在预判时以 `audit_flags=["notes_workfile_changed"]` 体现

## 6. 默认重跑规则

P2 默认采用“最小模式”：

- 自动重跑只由文档变化、engine 版本变化、或无成功历史触发
- `notes_workfile` 变化与 `knowledge_base` 版本变化只做审计，不自动要求重跑

### 6.1 `needs_rerun=true`

出现以下任一情况即为 `true`：

1. registry 中没有该 `report_key`
2. 该报告没有任何成功 attempt
3. 最新已知 attempt 为失败，且之后没有新的成功
4. 当前任务的 `document_fingerprint` 不等于最近一次成功的 `document_fingerprint`
5. 当前目标 `engine_version` 不等于最近一次成功的 `engine_version`

对应 `rerun_reasons` 可能包括：

- `report_not_in_registry`
- `no_successful_attempt`
- `latest_attempt_failed`
- `document_fingerprint_changed`
- `engine_version_changed`

### 6.2 `needs_rerun=false`

以下变化不会单独触发自动重跑：

- 仅 `notes_workfile_fingerprint` 变化
- 仅 `knowledge_base_version` 变化

这两类变化写入：

- `audit_flags=["notes_workfile_changed"]`
- `audit_flags=["knowledge_base_version_changed"]`

### 6.3 `knowledge_base_version` 口径

P2 只复用：

- [runtime/knowledge/knowledge_base.json](/Users/yetim/project/financialanalysis/runtime/knowledge/knowledge_base.json)

中的：

- `metadata.version`

作为审计字段。

P2 不因为 `knowledge_base` 版本变化自动认定必须重跑。

## 7. 与 Batch 产物的关系

### 7.1 `task_results.jsonl`

`run_batch_pipeline.py` 在每条 task result 中补充 registry 相关字段：

- `registry_report_key`
- `registry_document_fingerprint`
- `registry_processing_fingerprint`
- `registry_attempt_id`
- `registry_needs_rerun`
- `registry_rerun_reasons`
- `registry_audit_flags`
- `registry_decision`

`registry_decision` 可能包括：

- `selected_for_run`
- `skipped_existing_success_in_batch`
- `skipped_existing_success_in_registry`
- `filtered_out_not_failed`

### 7.2 `batch_manifest.json`

`batch_manifest.json` 新增：

- 顶层 `registry`
  - `registry_path`
  - `schema_version`
  - `updated_at`
  - `stats`
  - `knowledge_base_version`
  - `engine_version`
  - `backfill_performed_on_init`
  - `init_warnings`

`task_index` 中每个任务新增：

- `registry_report_key`
- `registry_decision`
- `registry_needs_rerun`

### 7.3 `--resume` 判定顺序

P2 后 `--resume` 顺序调整为：

1. 先看当前批次 `task_results.jsonl` 是否已有成功记录
2. 再看全局 processed reports registry
3. 只有“当前文档版本已被当前 `engine_version` 成功处理且无重跑原因”才跳过

这意味着：

- 不再只依赖 `task_id`
- 跨批次也可以跳过已稳定处理的同一份文档
- 若文档已变化或 engine 已升级，即使本批次或历史批次曾成功，也会重新执行

## 8. 历史回填规则

首次创建 registry 时自动回填：

### 8.1 W6 回填

扫描：

- `financial-analyzer/test_runs/w6_*/run_manifest.json`

规则：

- 成功态与失败态都回填
- 统一记为 `source_kind=legacy_single_run`
- `task_id` 默认取运行目录名

### 8.2 W7 回填

扫描：

- `financial-analyzer/test_runs/batches/*`

要求：

- `task_results.jsonl` 存在
- 每条记录里的 `manifest_path` 真实存在

规则：

- 每个 task result 关联其 `batch_manifest.json` 和 `task_results.jsonl`
- 统一记为 `source_kind=batch_task`

### 8.3 W7 缺失目录

若仓库内只存在：

- `financial-analyzer/test_runs/w7_batch_regression_results.json`

但不存在真实的：

- `financial-analyzer/test_runs/batches/`

则：

- 输出 warning
- 不报错
- 不伪造 batch manifest/task results 关系

## 9. 写入与并发

registry 写入规则：

- 相邻锁文件：`processed_reports.lock`
- 获取锁超时：30 秒
- 超时后直接失败退出，不静默覆盖
- JSON 写入采用临时文件 + `replace` 的原子写入方式

首次回填与后续 batch 更新都走同一套写入逻辑。

## 10. 当前实现边界

P2 当前已实现：

- runtime helper
- processed reports registry helper
- W7 batch runner 接入
- W6/W7 历史回填
- P2 专项回归脚本

P2 当前不做：

- 多 schema 自动迁移
- 因 `knowledge_base` 变化触发自动重跑
- 在 `knowledge_manager.py` 中直接承载 registry 写入

## 11. 与其他文档的关系

- [runtime_external_data_layer_spec.md](/Users/yetim/project/financialanalysis/runtime_external_data_layer_spec.md)
  - 负责说明 runtime、Git 边界和正式路径
- 本文档
  - 负责说明 processed reports registry 的 schema、规则与更新流程
- [production_execution_runbook.md](/Users/yetim/project/financialanalysis/production_execution_runbook.md)
  - 负责说明 P2 线程在生产化阶段中的位置与执行顺序
