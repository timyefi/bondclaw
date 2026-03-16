# Open Record Protocol

## 目标

用稳定外壳承载每次运行的核心产物，同时允许章节、主题、字段和规则通过扩展载荷持续增长。

## 章节记录

`chapter_records.jsonl` 每行一条记录，固定核心字段如下：

- `chapter_no`
- `chapter_title`
- `status`
- `summary`

扩展载荷如下：

- `attributes`
- `numeric_data`
- `findings`
- `anomalies`
- `evidence`
- `extensions`

记录范围仅限“已确认附注主章节”，正文不进入 `chapter_records.jsonl`。
`attributes` 至少补充：

- `note_no`
- `note_scope`
- `locator_evidence`

读取旧记录时，只依赖固定核心字段；扩展字段缺失不能导致失败。

## 重点列表

`focus_list.json` 固定核心字段如下：

- `focus_name`
- `why_selected`
- `evidence_chapters`

扩展字段如下：

- `focus_attributes`
- `related_topics`
- `knowledge_gap`
- `impact_scope`

## 最终数据

`final_data.json` 固定核心字段如下：

- `entity_profile`
- `key_conclusions`
- `topic_results`

各主题节点允许通过 `attributes` 和 `extensions` 自由增长。

## 运行清单

`run_manifest.json` 需要显式记录附注工作流结果：

- `status`
- `failure_reason`
- `notes_locator`
- `notes_catalog_summary`

失败时只写失败态 `run_manifest.json`，不写正常分析产物。

## 待固化更新

`pending_updates.json` 只记录候选项，不直接污染正式知识库。每项必须带以下元数据：

- `source`
- `evidence`
- `applicable_scope`
- `status`
- `introduced_in`
- `confidence`

缺失元数据的候选项只能视为临时笔记，不能升级为正式能力。
