# W6 Regression Report

- 生成时间：2026-03-18T14:40:16+08:00
- 结果 JSON：`/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_regression_results.json`
- 匹配情况：5/5 matched
- 成功案例：3
- 失败案例：2
- Golden Diff：clean=5, diff=0, skipped=0

## 验证范围

- 固定 3 个成功案例重跑 `financial_analyzer.py`，并验证 `run_manifest.json`、`chapter_records.jsonl`、`analysis_report_scaffold.md`、`focus_list_scaffold.json`、`final_data_scaffold.json`、`soul_export_payload_scaffold.json`。
- 固定 3 个成功案例还需确认 `analysis_report.md`、`final_data.json`、`soul_export_payload.json`、`financial_output.xlsx`、`preview.pdf`、`preview-*.png` 均未生成。
- 固定 2 个失败案例重跑 `financial_analyzer.py`，并验证失败态 `run_manifest.json`、失败原因和所有 scaffold / 正式产物缺失。
- Golden diff 仅评估受控 payload/manifest 子集，不把 diff 作为退出码门禁。
- 不把历史 `test_runs` 目录作为通过依据。

## 成功案例

### 恒隆地产 (`henglong`) - MATCHED

- expected_outcome: `success`
- run dir: `/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_henglong`
- markdown: `/Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md`
- notes_workfile: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/henglong_notes_workfile.json`
- expected_returncode: `0`
- returncode: `0`

#### Checks

- `run_manifest`: PASS
- `scaffold_outputs_present`: PASS
- `analysis_report_scaffold`: PASS
- `soul_export_payload_scaffold`: PASS
- `formal_outputs_absent`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_henglong
[OK] 章节记录: 4
[OK] scaffold 初步重点: 6
[OK] script_output_mode: scaffold_only
✅ 成功: 抽取与 scaffold 已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_henglong
```

### 碧桂园 (`country_garden`) - MATCHED

- expected_outcome: `success`
- run dir: `/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden`
- markdown: `/Users/yetim/project/financialanalysis/cases/碧桂园2024年年报分析.md`
- notes_workfile: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/country_garden_notes_workfile.json`
- expected_returncode: `0`
- returncode: `0`

#### Checks

- `run_manifest`: PASS
- `scaffold_outputs_present`: PASS
- `analysis_report_scaffold`: PASS
- `soul_export_payload_scaffold`: PASS
- `formal_outputs_absent`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/cases/碧桂园2024年年报分析.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden
[OK] 章节记录: 31
[OK] scaffold 初步重点: 6
[OK] script_output_mode: scaffold_only
✅ 成功: 抽取与 scaffold 已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden
```

### 杭海新城控股 (`hanghai`) - MATCHED

- expected_outcome: `success`
- run dir: `/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_hanghai`
- markdown: `/Users/yetim/project/financialanalysis/cases/杭海新城控股2024年年报分析.md`
- notes_workfile: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/hanghai_notes_workfile.json`
- expected_returncode: `0`
- returncode: `0`

#### Checks

- `run_manifest`: PASS
- `scaffold_outputs_present`: PASS
- `analysis_report_scaffold`: PASS
- `soul_export_payload_scaffold`: PASS
- `formal_outputs_absent`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/cases/杭海新城控股2024年年报分析.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_hanghai
[OK] 章节记录: 7
[OK] scaffold 初步重点: 6
[OK] script_output_mode: scaffold_only
✅ 成功: 抽取与 scaffold 已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_hanghai
```

## 失败路径回归

### 恒隆地产 / 缺失 notes_workfile (`missing_notes_workfile`) - MATCHED

- expected_outcome: `failure`
- run dir: `/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_missing_notes_workfile`
- markdown: `/Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md`
- notes_workfile: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/missing_notes_workfile.json`
- expected_returncode: `1`
- returncode: `1`

#### Checks

- `run_manifest_failure`: PASS
- `formal_outputs_absent`: PASS
- `failure_outputs_absent`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_missing_notes_workfile
```

### 恒隆地产 / 无效 notes_workfile (`invalid_notes_workfile`) - MATCHED

- expected_outcome: `failure`
- run dir: `/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_invalid_notes_workfile`
- markdown: `/Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md`
- notes_workfile: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/henglong_notes_workfile_invalid.json`
- expected_returncode: `1`
- returncode: `1`

#### Checks

- `run_manifest_failure`: PASS
- `formal_outputs_absent`: PASS
- `failure_outputs_absent`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_invalid_notes_workfile
```

## Golden Diff 评估

### 恒隆地产 (`henglong`)

- `golden_success_subset`: `clean`
  - golden_path: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/w6_golden/henglong_success.json`

### 碧桂园 (`country_garden`)

- `golden_success_subset`: `clean`
  - golden_path: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/w6_golden/country_garden_success.json`

### 杭海新城控股 (`hanghai`)

- `golden_success_subset`: `clean`
  - golden_path: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/w6_golden/hanghai_success.json`

### 恒隆地产 / 缺失 notes_workfile (`missing_notes_workfile`)

- `golden_failure_subset`: `clean`
  - golden_path: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/w6_golden/missing_notes_workfile_failure.json`

### 恒隆地产 / 无效 notes_workfile (`invalid_notes_workfile`)

- `golden_failure_subset`: `clean`
  - golden_path: `/Users/yetim/project/financialanalysis/financial-analyzer/testdata/w6_golden/invalid_notes_workfile_failure.json`

## 已知缺口

### 历史 run_manifest 仍保留 Windows 绝对路径

- 分类：`observed_repo_state`
- 说明：历史 test_runs 样本不能直接作为当前 W6 基线，因为 artifacts 仍指向旧环境路径。
- 证据：
  - `{"case_id": "henglong_notes_only", "path": "C:\\Users\\Administrator\\Desktop\\项目\\信用工作流\\年报训练\\financial-analyzer\\test_runs\\henglong_notes_only\\run_manifest.json"}`
  - `{"case_id": "henglong_v3", "path": "C:\\Users\\Administrator\\Desktop\\项目\\信用工作流\\年报训练\\financial-analyzer\\test_runs\\henglong_v3\\run_manifest.json"}`

### henglong_v3 缺少正式 status 字段

- 分类：`observed_repo_state`
- 说明：该目录可作为历史排障样本，但不能继续充当成功态回归基线。
- 证据：
  - `{"case_id": "henglong_v3", "manifest_path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/henglong_v3/run_manifest.json"}`

### 历史目录同时存在旧内部 workbook 与新 Soul workbook

- 分类：`observed_repo_state`
- 说明：历史目录仍混有旧 workbook 样本；当前 W6 已切换为 scaffold-only，不再用旧 workbook 作为模板脚本成功依据。
- 证据：
  - `{"path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/henglong_soul_contract/financial_output.xlsx", "sheetnames": ["summary", "focus", "chapters", "topic_results", "pending_updates"]}`
  - `{"path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/henglong_soul_v1_1_alpha/soul_output.xlsx", "sheetnames": ["00_overview", "01_kpi_dashboard", "02_financial_summary", "03_debt_profile", "04_liquidity_and_covenants", "05_bond_detail", "08_topic_investment_property", "99_evidence_index"]}`

### 模板脚本不再把 preview 作为主门禁

- 分类：`known_scope_boundary`
- 说明：当前模板脚本只负责 scaffold 产物；preview.pdf / preview-*.png 已从 W6 成功态门禁中移出，不再作为模板脚本验收项。
