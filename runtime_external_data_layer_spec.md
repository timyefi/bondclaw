# Runtime 外部数据层规范（P1）

## 1. 文档定位

本文档是生产化阶段 P1 的正式规范，解决以下问题：

1. 正式投入使用后，哪些内容属于 `skill`，哪些属于 `runtime`，哪些只属于治理文档。
2. 正式生产默认 `runtime` 根目录放在哪里，哪些内容进入 Git，哪些内容不得进入 Git。
3. `runtime_config` 应如何描述项目内可携带的 runtime 路径。
4. 后续 P2/P3/P5 线程应基于什么路径口径继续实现。

本文档只定义运行时数据层与边界，不实现 registry schema、skill 绑定代码或 10 案测试。

## 2. 三层分工原则

### 2.1 `skill` 负责能力定义

`skill` 目录及其 `SKILL.md`、`references/`、模板文件只负责：

- 能力边界
- 固定流程
- 稳定输入输出契约
- 治理要求与人工流程说明

`skill` 不负责：

- 生产批次动态状态
- 自发改写自身文档
- 持续增长的 registry、日志、审核结果

### 2.2 `runtime` 负责动态数据

`runtime` 负责承载生产运行过程中的动态数据，包括：

- 正式 `runtime_config`
- 正式 `knowledge_base`
- 全局 processed reports registry
- 批次运行产物
- review bundle、日志、临时文件

### 2.3 文档负责治理说明

项目文档负责：

- 路径治理口径
- 目录与配置契约
- 哪些内容进 Git、哪些不进 Git
- 人工审核和后续线程执行约束

文档本身不作为运行时即时生效的数据源。

## 3. 正式生产默认路径策略

本项目正式生产默认采用“项目内可携带 runtime”方案：

- 默认 `runtime` 根目录：`/Users/yetim/project/financialanalysis/runtime/`
- 目标：方便与仓库一起迁移、复制和在其他环境快速部署
- 约束：不把全部运行态数据纳入 Git

结论：

- `runtime` 放在项目内
- `runtime_config + knowledge_base + adoption_logs 骨架` 进入 Git
- `registry / batches / governance_review / logs / tmp` 视为运行态状态目录，不进入 Git

## 4. 正式目录结构

推荐目录结构如下：

```text
runtime/
  README.md
  runtime_config.json
  knowledge/
    knowledge_base.json
    adoption_logs/
      .gitkeep
  state/
    registry/
      processed_reports/
        processed_reports.json
        snapshots/
    batches/
    governance_review/
    logs/
    tmp/
```

各目录用途如下：

- `runtime/README.md`
  - 说明项目内 runtime 的边界、Git 策略和后续线程应读取的规范。
- `runtime/runtime_config.json`
  - 正式生产默认配置入口。
- `runtime/knowledge/knowledge_base.json`
  - 正式知识基线，允许进入 Git。
- `runtime/knowledge/adoption_logs/`
  - 人工采纳流程的目录骨架；是否提交具体日志由后续治理策略决定，P1 只保留目录骨架。
- `runtime/state/registry/processed_reports/processed_reports.json`
  - 全局 processed reports registry 正式落点。
- `runtime/state/batches/`
  - 批次运行目录根路径。
- `runtime/state/governance_review/`
  - 审核包、人工 review 中间产物的生产态落点。
- `runtime/state/logs/`
  - 运行日志根路径。
- `runtime/state/tmp/`
  - 临时文件目录。

## 5. Git 跟踪边界

### 5.1 应进入 Git 的内容

- `runtime/runtime_config.json`
- `runtime/knowledge/knowledge_base.json`
- `runtime/knowledge/adoption_logs/` 目录骨架
- `runtime/README.md`

这些内容的共同特征是：

- 低频变更
- 需要审阅
- 可作为跨环境携带的静态基线

### 5.2 不应进入 Git 的内容

- `runtime/state/registry/**`
- `runtime/state/batches/**`
- `runtime/state/governance_review/**`
- `runtime/state/logs/**`
- `runtime/state/tmp/**`

这些内容的共同特征是：

- 高频变化
- 与具体机器、具体批次、具体操作时序绑定
- 容易造成仓库膨胀与历史噪声

### 5.3 当前 P1 的实现边界

P1 只定义上述 Git 边界与目录口径：

- 不实现 `.gitignore`
- 不修改现有脚本默认路径
- 不实现 registry 读写
- 不启动批次测试

## 6. `runtime_config` 契约

### 6.1 文件位置

正式生产默认配置文件固定为：

- [runtime/runtime_config.json](/Users/yetim/project/financialanalysis/runtime/runtime_config.json)

### 6.2 推荐结构

```json
{
  "contract_version": "runtime_config_v1",
  "runtime_id": "financialanalysis_repo_runtime",
  "runtime_mode": "project_local",
  "project_root": "/abs/path/to/repo",
  "runtime_root": "/abs/path/to/repo/runtime",
  "paths": {
    "knowledge_base": "runtime/knowledge/knowledge_base.json",
    "knowledge_adoption_log_dir": "runtime/knowledge/adoption_logs",
    "processed_reports_registry": "runtime/state/registry/processed_reports/processed_reports.json",
    "batch_root": "runtime/state/batches",
    "governance_review_root": "runtime/state/governance_review",
    "logs_root": "runtime/state/logs",
    "tmp_root": "runtime/state/tmp"
  },
  "policies": {
    "require_paths_under_project_root": true,
    "knowledge_base_tracked_in_git": true,
    "runtime_state_tracked_in_git": false,
    "forbid_skill_dir_writes": true
  }
}
```

### 6.3 契约规则

- `contract_version` 用于后续版本兼容。
- `runtime_mode` 在当前阶段固定为 `project_local`。
- `project_root`、`runtime_root` 使用绝对路径。
- `paths.*` 优先使用相对 `project_root` 的可搬运相对路径。
- 所有运行时读写路径都必须落在项目根目录下。
- `knowledge_base` 允许进入 Git。
- `processed_reports_registry`、`batch_root`、`governance_review_root`、`logs_root`、`tmp_root` 不进入 Git。
- `runtime_config` 不承载批次级动态状态，也不承载 secrets。

## 7. 正式落点

### 7.1 `knowledge_base`

正式推荐落点：

- [runtime/knowledge/knowledge_base.json](/Users/yetim/project/financialanalysis/runtime/knowledge/knowledge_base.json)

治理口径：

- 这是正式知识基线，允许进入 Git。
- 应视为“受治理、低频变更、可审阅”的资产。
- 后续知识 apply 流程应更新这里，而不是继续写仓库旧位置。

### 7.2 全局 registry

正式推荐落点：

- [runtime/state/registry/processed_reports/processed_reports.json](/Users/yetim/project/financialanalysis/runtime/state/registry/processed_reports/processed_reports.json)

治理口径：

- 这是高频状态表，不进入 Git。
- P2 线程必须以此为唯一正式落点设计 schema 和更新流程。
- P2 的正式 schema、去重/重跑规则与 batch 关系见 [processed_reports_registry_spec.md](/Users/yetim/project/financialanalysis/processed_reports_registry_spec.md)。

### 7.3 批次产物

正式推荐落点：

- [runtime/state/batches](/Users/yetim/project/financialanalysis/runtime/state/batches)

批次目录下应继续承接现有 W7 产物形态，包括：

- `batch_manifest.json`
- `task_results.jsonl`
- `failed_tasks.json`
- `pending_updates_index.json`
- `governance_review/`
- `tasks/<task_id>/...`

这意味着后续如果把 [financial-analyzer/scripts/run_batch_pipeline.py](/Users/yetim/project/financialanalysis/financial-analyzer/scripts/run_batch_pipeline.py) 接入正式 production runtime，其默认批次根目录应映射到 `runtime/state/batches/`，而不是仓库内 `financial-analyzer/test_runs/batches/`。

## 8. 与当前仓库事实的关系

### 8.1 当前旧位置

当前仓库中的旧知识库位置为：

- [financial-analyzer/knowledge_base.json](/Users/yetim/project/financialanalysis/financial-analyzer/knowledge_base.json)

P1 对它的定位调整为：

- 历史位置
- 迁移源
- 兼容过渡期基线

P1 不修改脚本引用，也不实现自动迁移。

### 8.2 回归目录与生产目录的区别

当前仓库中的：

- [financial-analyzer/test_runs](/Users/yetim/project/financialanalysis/financial-analyzer/test_runs)

继续视为：

- 回归样本目录
- 手工验证目录
- 历史对照目录

不再视为正式生产 runtime 根目录。

## 9. 绝不能写进 `~/.codex/skills` 的内容

以下内容一律不得写进 `~/.codex/skills`：

- 任意 `runtime_config`
- 任意 `knowledge_base` 运行态副本
- 任意 registry
- 任意批次目录和单案产物
- 任意 `pending_updates` 审核包与人工决议
- 任意日志、缓存、锁文件、快照
- 任意机器相关绝对路径
- 运行中对 `SKILL.md` 的自发改写
- 运行中对 `references/*.md` 的自发改写

原则是：

- `skill` 负责能力定义
- `runtime` 负责动态数据
- 文档负责治理说明

## 10. 对后续线程的约束

### 10.1 对 P2 的约束

- P2 只能把 processed reports registry 设计在 `runtime/state/registry/processed_reports/` 下。
- 不得再把 registry 放到 `financial-analyzer/test_runs/` 或 `~/.codex/skills/`。

### 10.2 对 P3 的约束

- P3 的 `runtime_config` 发现与绑定逻辑，必须以 [runtime/runtime_config.json](/Users/yetim/project/financialanalysis/runtime/runtime_config.json) 为正式项目内入口。
- 不得要求 skill 在运行时自发改写自己的 `SKILL.md` 或 reference 文档。

### 10.3 对 P5 的约束

- 冷启动仿真时，应优先检查 `runtime/runtime_config.json` 是否存在、路径是否可写、生产态目录是否已准备。
- 批次仿真目录必须落到 `runtime/state/batches/`，而不是测试回归目录。

## 11. P1 完成判定

满足以下条件即可视为 P1 方案已落地：

1. 有单独的 runtime 规范文档。
2. 文档明确 `runtime` 项目内落点与 Git 边界。
3. 文档明确 `runtime_config` 契约。
4. 文档明确 `knowledge_base`、registry、batches 的正式落点。
5. 文档明确哪些内容绝不能写进 `~/.codex/skills`。
6. 蓝图与生产化手册已同步到同一口径。
