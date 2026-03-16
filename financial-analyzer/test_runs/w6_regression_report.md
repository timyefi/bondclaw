# W6 Regression Report

- 生成时间：2026-03-17T07:43:16+08:00
- 结果 JSON：`/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_regression_results.json`
- 匹配情况：5/5 matched
- 成功案例：3
- 失败案例：2
- Golden Diff：clean=5, diff=0, skipped=0

## 验证范围

- 固定 3 个成功案例重跑 `financial_analyzer.py`，并验证 `run_manifest.json`、`analysis_report.md`、`soul_export_payload.json`、`financial_output.xlsx`、`preview.pdf`、`preview-*.png`。
- 固定 2 个失败案例重跑 `financial_analyzer.py`，并验证失败态 `run_manifest.json`、失败原因和成功态产物缺失。
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
- `analysis_report`: PASS
- `soul_export_payload`: PASS
- `financial_output`: PASS
- `workbook_preview`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/output/恒隆地产/恒隆地产2024年報/恒隆地产2024年報.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_henglong
[OK] 章节记录: 4
[OK] 动态重点: 6
[OK] 待固化更新: 9
✅ 成功: 产物已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_henglong
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
- `analysis_report`: PASS
- `soul_export_payload`: PASS
- `financial_output`: PASS
- `workbook_preview`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/cases/碧桂园2024年年报分析.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden
[OK] 章节记录: 31
[OK] 动态重点: 6
[OK] 待固化更新: 12
✅ 成功: 产物已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden
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
- `analysis_report`: PASS
- `soul_export_payload`: PASS
- `financial_output`: PASS
- `workbook_preview`: PASS

```text
[INFO] 输入文件: /Users/yetim/project/financialanalysis/cases/杭海新城控股2024年年报分析.md
[INFO] 运行目录: /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_hanghai
[OK] 章节记录: 7
[OK] 动态重点: 6
[OK] 待固化更新: 12
✅ 成功: 产物已生成 -> /Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_hanghai
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
- 说明：W6 只认当前脚本重跑后的 financial_output.xlsx，不直接以历史目录判定通过。
- 证据：
  - `{"path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/henglong_soul_contract/financial_output.xlsx", "sheetnames": ["summary", "focus", "chapters", "topic_results", "pending_updates"]}`
  - `{"path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/henglong_soul_v1_1_alpha/soul_output.xlsx", "sheetnames": ["00_overview", "01_kpi_dashboard", "02_financial_summary", "03_debt_profile", "04_liquidity_and_covenants", "05_bond_detail", "08_topic_investment_property", "99_evidence_index"]}`

### Workbook 单元格级 golden diff 仍暂缓

- 分类：`known_scope_boundary`
- 说明：当前 W6.1 仅冻结 payload/manifest 子集；`w6_country_garden` 的 `01_kpi_dashboard` 仍存在 XML 值兼容性问题，暂不做整本或逐单元格 golden。
- 证据：
  - `{"path": "/Users/yetim/project/financialanalysis/financial-analyzer/test_runs/w6_country_garden/financial_output.xlsx", "sheet_name": "01_kpi_dashboard", "worksheet_xml": "xl/worksheets/sheet2.xml"}`

### 当前预览检查只覆盖结构，不覆盖版式语义

- 分类：`known_scope_boundary`
- 说明：W6.1 只校验 preview 产物存在性、连续编号和尺寸一致性，不判断分页质量、内容遮挡或视觉美观。
