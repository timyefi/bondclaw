# Codex 执行手册（对话启动清单）

## 1. 这份文档解决什么问题

这份文档用于把总蓝图转成可执行的 Codex 工作方式，解决以下问题：

1. 新对话应该从哪里开始。
2. 一个对话到底做多大范围。
3. 多个对话之间如何交接，避免重复解释和上下文漂移。
4. 后续如果启用多个 agent，应该按什么顺序推进。

它不是项目蓝图的替代品，而是蓝图的执行说明书。整体设计仍以 `automation_blueprint.md` 为准。

## 2. 推荐工作模式

本项目建议采用“1 个总控线程 + 多个执行线程”的工作方式。

### 2.0 Git 基线

本项目当前采用单分支策略：

1. 本地默认只保留 `main`
2. 远程默认只保留 `origin/main`
3. 新对话默认直接在 `main` 上工作
4. 除非用户明确要求，否则不要创建新的 `codex/*` 或其他长期分支

这意味着“多个执行线程”是多个 Codex 对话，不是多个长期 Git 分支。

### 2.1 总控线程

用途：

- 只负责项目编排、任务排序、状态同步、跨线程交接。
- 不承担大规模代码实现。

适合做的事情：

- 决定下一个执行线程处理哪个 workstream
- 判断是否需要更新蓝图
- 整理阶段状态和优先级
- 审查某个执行线程的结果是否可以进入下一阶段

### 2.2 执行线程

用途：

- 每个线程只做一个主任务，必须有明确交付物。

强约束：

1. 一个线程只聚焦一个主 workstream。
2. 一个线程只追求一个主交付物。
3. 避免在同一线程里同时改采集、解析、分析、Excel、编排。

## 3. 什么时候要新开对话

满足以下任一条件，就应该新开对话，而不是继续在旧线程里叠加：

1. 主目标已经从“设计”切换到“实现”。
2. 当前任务开始跨越另一个 workstream。
3. 需要读取的上下文已经明显变多。
4. 需要交给另一个 agent 独立执行。
5. 已经形成一个可交付物，可以进入下一个阶段。

## 4. 推荐执行顺序

当前建议不要并行太多，按以下顺序推进：

| 顺序 | 类型 | Workstream | 主目标 | 交付物 |
|------|------|------------|--------|--------|
| 0 | 总控线程 | PM | 维护蓝图、排序任务、审查结果 | 状态更新、下一步安排 |
| 1 | 执行线程 | W4 | 设计 Soul 数据契约 | 契约文档 + 样例 JSON |
| 2 | 执行线程 | W4 | 双案例 Soul 模板打样 | 2 个样稿 Excel + 差异总结 |
| 3 | 执行线程 | W3/W4 | 拆分 Financial Analysis 与 Soul 导出层 | 代码改造 + 跑通产物 |
| 4 | 执行线程 | W6 | 建立回归与质量检查 | 回归脚本/说明 + 验证结果 |
| 5 | 执行线程 | W7 | 任务编排与批处理 | 编排方案或入口脚本 |

说明：

- 当前最应该先开的，是顺序 1 的 W4 契约设计线程。
- W7 不要过早开始，否则容易在未稳定的结构上做无效编排。

## 5. 每次新线程的标准开场动作

任何新的执行线程，默认先做以下动作：

1. 阅读 `AGENTS.md`
2. 阅读 `automation_blueprint.md`
3. 阅读与本线程直接相关的专项文档
4. 确认当前 Git 分支是 `main`
5. 用一句话确认当前线程属于哪个 workstream
6. 用一句话确认本线程的唯一主交付物

## 5.1 你实际怎么操作 Git

如果你后面自己开新对话并在完成后提交推送，最简单的固定流程就是：

1. 先确认在 `main`
2. 拉取最新 `main`
3. 让 Codex 完成修改
4. 运行必要验证
5. 提交到 `main`
6. 推送 `main`

推荐命令：

```bash
git checkout main
git pull --ff-only origin main
git status --short
git add <files>
git commit -m "feat: ..."
git push origin main
```

如果你想在提交前再确认一次自己没有偏离单分支策略，可以加两步：

```bash
git branch -vv
git branch -r
```

你应当看到本地只有 `main`，远程只有 `origin/main`。

## 5.2 提交前检查

每次准备提交前，至少检查：

1. `git branch -vv` 显示当前在 `main`
2. `git status --short` 只包含你预期的改动
3. 必要验证命令已经跑过
4. 本次对话如果涉及结构性决策，相关文档已同步更新

## 5.3 推送后检查

每次推送后，建议检查：

```bash
git fetch origin
git branch -vv
git branch -r
```

目标状态：

- 本地：只有 `main`
- 远程：只有 `origin/main`
- `main` 不显示 `ahead` 或 `behind`

## 6. 推荐线程卡片

以下是建议直接开设的 5 个线程。

## 6.1 线程 A：W4 / Soul 数据契约设计

### 目标

- 定义 Financial Analysis 应输出什么稳定契约，才能被 Soul 导出层稳定消费。

### 开始前阅读

- `automation_blueprint.md`
- `soul_excel_spec_v1.md`
- `soul_excel_case_analysis.md`
- `excel_skill_adoption_plan.md`

### 输入

- 现有 `financial-analyzer/scripts/financial_analyzer.py` 的输出结构
- Soul 固定骨架与可选模块定义
- 历史案例 Excel

### 本线程不做

- 不直接改最终模板样式
- 不实现批处理
- 不同时重构 MinerU 或下载层

### 交付物

- Soul 数据契约文档
- 样例 JSON
- 核心字段与可选模块字段说明

### 验收标准

1. 能覆盖固定骨架和可选模块。
2. 能明确区分对外交付字段和内部字段。
3. 能支持后续双案例打样。

### 可直接复制的提示词

```text
先阅读 AGENTS.md、automation_blueprint.md、soul_excel_spec_v1.md、soul_excel_case_analysis.md、excel_skill_adoption_plan.md。当前聚焦 W4。请设计 Soul 导出数据契约，要求覆盖固定骨架和可选模块，并给出样例 JSON、字段说明和与现有 financial_analyzer 输出的映射方案。不要处理下载、MinerU 或批处理。
```

## 6.2 线程 B：W4 / 双案例 Soul 模板打样

### 目标

- 用两个差异较大的案例验证 Soul 模块化结构能否落地。

### 开始前阅读

- `automation_blueprint.md`
- `soul_excel_spec_v1.md`
- `excel_skill_adoption_plan.md`
- 数据契约文档

### 建议样本

- 恒隆地产
- 杭海新城控股

### 本线程不做

- 不修改下载或解析链路
- 不顺手重构 `financial_analyzer.py`
- 不提前做批量编排

### 交付物

- 2 个 Soul v1.1-alpha 样稿 Excel
- 模块复用情况总结
- 样式与结构需调整的清单

### 验收标准

1. 两个案例都能落在同一骨架下。
2. 专题模块确实只承载差异，不污染主结构。
3. 能看出固定骨架是否还缺字段。

### 可直接复制的提示词

```text
先阅读 AGENTS.md、automation_blueprint.md、soul_excel_spec_v1.md、excel_skill_adoption_plan.md，以及最新的 Soul 数据契约文档。当前聚焦 W4。请基于恒隆地产和杭海新城控股两个案例，生成 Soul v1.1-alpha 模板打样，重点验证固定骨架和专题模块。不要处理下载、MinerU 或批处理。
```

## 6.3 线程 C：W3/W4 / Financial Analysis 与 Soul 导出分层

### 目标

- 让分析引擎不再直接硬编码最终 Excel 成品结构，而是先输出稳定契约，再交给 Soul 导出层。

### 开始前阅读

- `automation_blueprint.md`
- Soul 数据契约文档
- `excel_skill_adoption_plan.md`
- `financial-analyzer/scripts/financial_analyzer.py`

### 本线程不做

- 不重做 Soul 结构设计
- 不同时改下载器和 MinerU
- 不开始批量调度

### 交付物

- 代码改造
- 运行命令
- 至少 1 个案例跑通结果

### 验收标准

1. `financial_analyzer.py` 可以输出稳定契约。
2. Soul 导出层独立生成 Excel。
3. `run_manifest.json` 与既有运行治理机制不被破坏。

### 可直接复制的提示词

```text
先阅读 AGENTS.md、automation_blueprint.md、excel_skill_adoption_plan.md，以及最新的 Soul 数据契约文档。当前聚焦 W3/W4 交界。请将 financial_analyzer 的最终 Excel 导出改为“先输出稳定契约，再调用独立 Soul 导出层”，并至少跑通 1 个案例验证。
```

## 6.4 线程 D：W6 / 回归与质量检查

### 目标

- 建立最小可用的回归流程，保证案例可重复验证。

### 开始前阅读

- `automation_blueprint.md`
- `AGENTS.md`
- 最新导出分层实现

### 本线程不做

- 不重新设计 Soul 结构
- 不重做案例模板
- 不启动任务编排

### 交付物

- 回归检查说明或脚本
- 至少 2 个案例的验证结果

### 验收标准

1. 能验证 `run_manifest.json` 路径与状态。
2. 能验证 `analysis_report.md` 是否生成。
3. 能验证 Soul Excel 是否生成且核心 Sheet 存在。

### 可直接复制的提示词

```text
先阅读 AGENTS.md 和 automation_blueprint.md。当前聚焦 W6。请为当前链路建立最小可用的回归检查，至少覆盖 run_manifest、analysis_report 和 Soul Excel 的生成结果，并用两个案例做验证。
```

## 6.5 线程 E：W7 / 编排与批处理

### 目标

- 在前面链路基本稳定后，再把任务清单批量跑起来。

### 开始前阅读

- `automation_blueprint.md`
- 最新回归与导出分层实现

### 本线程不做

- 不重构 Soul 结构
- 不修改数据契约
- 不修补前面阶段的大量历史问题

### 交付物

- 编排方案
- 任务队列格式
- 批处理入口脚本或设计说明

### 验收标准

1. 能定义任务清单格式。
2. 能串起下载、解析、分析、导出。
3. 能处理失败重试或失败记录。

### 可直接复制的提示词

```text
先阅读 AGENTS.md 和 automation_blueprint.md。当前聚焦 W7。请基于现有稳定链路设计任务编排与批处理入口，要求支持任务清单、失败记录和后续扩展，但不要重新设计 Soul 结构或数据契约。
```

## 7. 线程完成后的收尾动作

每个执行线程结束前，默认执行以下收尾：

1. 写清楚本线程完成了什么。
2. 写清楚没有完成什么。
3. 给出下一线程的建议起点。
4. 更新相关规范文档。
5. 更新 `automation_blueprint.md` 的状态区。

## 8. 常见错误顺序

以下顺序通常会导致返工：

1. 先做批处理，再做数据契约。
2. 先写复杂模板，再确定 Soul 骨架。
3. 在一个线程里同时重做分析逻辑和 Excel 结构。
4. 没有更新蓝图，只把决策留在对话里。
5. 为了开多个 Codex 对话而创建多个长期 Git 分支。

## 9. 建议你现在就怎么开始

如果你要立刻开下一个执行线程，建议从以下这一句开始：

```text
先阅读 AGENTS.md、automation_blueprint.md、soul_excel_spec_v1.md、soul_excel_case_analysis.md、excel_skill_adoption_plan.md。当前聚焦 W4。请设计 Soul 导出数据契约，要求覆盖固定骨架和可选模块，并给出样例 JSON、字段说明和与现有 financial_analyzer 输出的映射方案。不要处理下载、MinerU 或批处理。
```

这是当前最上游、最能减少后续返工的一步。
