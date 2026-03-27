# Codex 执行手册（对话启动清单）

## 1. 这份文档解决什么问题

这份文档用于把总蓝图转成可执行的 Codex 工作方式，解决以下问题：

1. 新对话应该从哪里开始。
2. 一个对话到底做多大范围。
3. 多个对话之间如何交接，避免重复解释和上下文漂移。
4. 后续如果启用多个 agent，应该按什么顺序推进。

它不是项目蓝图的替代品，而是蓝图的执行说明书。整体设计仍以 `automation_blueprint.md` 为准。

如果项目已完成 W1-W7 主线、并且当前口径已经切换为 scaffold-only + 直写式知识采纳，则继续阅读 `codex_review_and_finalization_runbook.md` 与 `production_execution_runbook.md`，不要沿用本手册中的早期 W5/W6.1/W7 顺序来组织后续任务。

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

### 2.3 Subagents 使用原则

`subagents` 适合做边界清晰、可以并行汇总的子任务，不适合多人同时改同一个核心入口文件或同一个最终规范。

当前项目建议如下：

1. 主线程仍负责最终决策、主文档更新和核心入口整合。
2. `subagents` 优先用于并行读取案例、汇总差异、验证失败路径、设计 QA 检查项。
3. 不要让多个 `subagents` 同时改同一个主脚本、同一个契约文件或同一个批处理入口。
4. 如果使用 `subagents`，主线程结束前仍应统一回写 `automation_blueprint.md` 和相关规范文档。

## 3. 什么时候要新开对话

满足以下任一条件，就应该新开对话，而不是继续在旧线程里叠加：

1. 主目标已经从“设计”切换到“实现”。
2. 当前任务开始跨越另一个 workstream。
3. 需要读取的上下文已经明显变多。
4. 需要交给另一个 agent 独立执行。
5. 已经形成一个可交付物，可以进入下一个阶段。

## 4. 当前剩余执行顺序

基于当前仓库进展，W4 契约、W4 模板打样、W3/W4 导出分层、W6 最小回归和 scaffold-only 口径都已经落地；R1 与 R2 的控制面与契约已经收口，当前主线应切到 R3 / P6，建议如下：

| 顺序 | 类型 | Workstream | 主目标 | 交付物 |
|------|------|------------|--------|--------|
| 0 | 总控线程 | PM | 维护蓝图、排序任务、审查结果 | 状态更新、下一步安排 |
| 1 | 执行线程 | R3 | 做 1-2 个完整案例演练 | scaffold -> 复核 -> 直写 -> formalization |
| 2 | 执行线程 | P6 | 形成 go-live checklist | 上线门禁、人工复核点、停机/回滚策略 |

说明：

- W4、W3/W4 和 W6 基线不是取消，而是已完成的上游阶段；只有发现回归问题时才回头重开。
- `R1` 和 `R2` 已经完成控制面与契约收口，后续线程直接消费文档即可。
- `R3` 是最小的真实演练，先用 1-2 个案例把 scaffold -> review -> adopt -> formalization 跑通。
- `P6` 只有在 `R3` 收敛后才适合执行，否则 go-live checklist 只能写成空清单。

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

以下线程卡片分为两类：

- 历史已完成参考：用于回溯已经落地的阶段
- 当前优先线程：用于你现在继续往下推进

## 6.1 线程 A：W4 / Soul 数据契约设计（已完成参考）

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

## 6.2 线程 B：W4 / 双案例 Soul 模板打样（已完成参考）

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

## 6.3 线程 C：W3/W4 / Financial Analysis 与 Soul 导出分层（已完成参考）

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

## 6.4 线程 D：W6 / 回归与质量检查（已完成参考）

### 目标

- 将当前已存在的多案例产物收敛为可重复执行的回归检查，而不只是一次性验证。

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
- 至少 3 个案例的验证结果
- 失败案例或已知缺口清单

### 验收标准

1. 能验证 `run_manifest.json` 路径与状态。
2. 能验证 `analysis_report.md` 是否生成。
3. 能验证 `soul_export_payload.json` 是否生成。
4. 能验证 Soul Excel 是否生成且核心 Sheet 存在。

### 可直接复制的提示词

```text
先阅读 AGENTS.md 和 automation_blueprint.md。当前聚焦 W6。请把现有多案例产物收敛为最小可用的回归检查，至少覆盖 run_manifest、analysis_report、soul_export_payload 和 Soul Excel 的生成结果，并用三个案例做验证，输出已知缺口清单。
```

## 6.5 线程 E：W5 / 知识进化与治理（已完成）

### 目标

- 在不污染 Soul 对外交付的前提下，为正式知识库建立最小可用的 Codex 直写与审计闭环。

### 开始前阅读

- `automation_blueprint.md`
- `financial-analyzer/SKILL.md`
- `financial-analyzer/references/output_contract.md`
- `financial-analyzer/references/open_record_protocol.md`
- `financial-analyzer/scripts/knowledge_manager.py`
- `financial-analyzer/scripts/write_knowledge_adoption.py`
- `financial-analyzer/scripts/rollback_knowledge_adoption.py`
- `financial-analyzer/scripts/show_knowledge_adoption.py`
- 至少 3 个案例的章节复核记录或 scaffold 产物

### 本线程不做

- 不直接把候选项批量写入 `knowledge_base.json`
- 不修改 Soul 固定骨架
- 不提前开始任务编排

### 交付物

- 多案例逐章复核摘要
- adoption log 规范
- 正式知识库直写与回滚入口说明
- 明确哪些知识增量应直接入库，哪些只保留案例级备注

### 验收标准

1. 能校验章节复核产物和知识增量元数据完整性。
2. 能识别跨案例重复出现的主题、字段、规则并形成可复用摘要。
3. 能把“案例观察”与“正式采纳”明确隔离。
4. 不会让 W5 的结果直接污染 Soul 导出契约。
5. 主线程能把直写、回滚和摘要规则回写到规范文档。

### 可直接复制的提示词

```text
先阅读 AGENTS.md、automation_blueprint.md、financial-analyzer/SKILL.md、financial-analyzer/references/output_contract.md、financial-analyzer/references/open_record_protocol.md，以及 financial-analyzer/scripts/knowledge_manager.py、write_knowledge_adoption.py、rollback_knowledge_adoption.py、show_knowledge_adoption.py。当前聚焦 W5。请基于至少三个案例的 scaffold 产物和章节复核记录，建立最小可用的知识直写闭环：完成知识增量校验、跨案例摘要、adoption log 规范和审核入口设计，但不要修改 Soul 结构。
```

## 6.6 线程 F：W6.1 / 更细粒度 QA（适合结合 Subagents,已完成）

### 目标

- 在 W6 最小回归已通过的基础上，补齐 scaffold-only 的失败路径回归、正式产物缺失检查和受控差异校验。

### 开始前阅读

- `automation_blueprint.md`
- `AGENTS.md`
- `financial-analyzer/scripts/run_w6_regression.py`
- 最近一次 `w6_regression_report.md`

### 推荐的 Subagents 拆法

1. 一个子线程专门补失败路径回归，例如 `missing_notes_workfile`
2. 一个子线程专门评估 scaffold 产物完整性和正式产物缺失
3. 一个子线程专门设计可持续的 golden diff 范围

主线程负责：

- 统一决定哪些检查正式纳入 W6.1
- 合并到主回归脚本或主 QA 说明
- 更新蓝图与执行手册

### 本线程不做

- 不重写 W5 升级规则
- 不提前开始批处理编排
- 不让多个子线程同时改同一个主回归入口

### 交付物

- W6.1 检查方案
- 至少一个新增失败路径回归
- scaffold 完整性或 golden diff 的落地建议
- 明确哪些检查先进入主线，哪些保留为后续增强

### 验收标准

1. 至少补上一条失败路径回归。
2. 能说明 scaffold-only 的正式产物缺失检查是否足够。
3. 能说明 golden diff 应比较哪些稳定字段，而不是比整个工作簿二进制。
4. 使用 `subagents` 时，主线程仍能统一收敛结果并更新文档。

### 可直接复制的提示词

```text
先阅读 AGENTS.md、automation_blueprint.md、financial-analyzer/scripts/run_w6_regression.py，以及最近一次 W6 回归结果。当前聚焦 W6.1。请在 W6 最小回归已通过的前提下，补齐失败路径回归、评估 scaffold-only 的正式产物缺失检查和 golden diff 范围；如果适合，请使用 subagents 并行处理这些子问题，但主线程要统一整合结果，不要多人同时改同一个主回归入口。
```

## 6.7 线程 G：W7 / 编排与批处理（已完成 v1）

### 目标

- 在前面链路基本稳定后，再把任务清单批量跑起来。

### 开始前阅读

- `automation_blueprint.md`
- 最新回归与导出分层实现
- W5 治理规则与审核边界

### 本线程不做

- 不重构 Soul 结构
- 不修改数据契约
- 不修补前面阶段的大量历史问题

### 交付物

- 编排方案
- 任务队列格式
- 批处理入口脚本或设计说明
- `financial-analyzer/scripts/run_batch_pipeline.py`
- `financial-analyzer/testdata/w7_batch_tasks/*.json`
- `financial-analyzer/scripts/run_w7_batch_regression.py`

### 验收标准

1. 能定义任务清单格式。
2. 能串起下载、解析、分析、导出。
3. 能处理失败重试或失败记录。
4. 能明确 scaffold 产物、正式产物与知识写入的交接边界。

### 可直接复制的提示词

```text
先阅读 AGENTS.md 和 automation_blueprint.md，以及最新的 W5 治理规则文档。当前聚焦 W7。请基于现有稳定链路设计任务编排与批处理入口，要求支持任务清单、失败记录、scaffold 产物和正式产物的交接边界，但不要重新设计 Soul 结构或数据契约。
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
6. 在 `W5` 直写与审计边界未明确前，就先把知识写入编进自动批处理。

## 9. 建议你现在就怎么开始

如果你现在需要继续主线程，建议下一步直接开 `R1`：

```text
先阅读 AGENTS.md、automation_blueprint.md、codex_review_and_finalization_runbook.md、financial-analyzer/SKILL.md、financial-analyzer/references/output_contract.md、financial-analyzer/references/open_record_protocol.md，以及 financial-analyzer/scripts/knowledge_manager.py、write_knowledge_adoption.py、rollback_knowledge_adoption.py、show_knowledge_adoption.py。当前聚焦 R1：Codex 复核与直写控制面。请基于 scaffold-only 口径，建立章节状态机、adoption gate、finalization gate 和回滚边界，但不要修改 Soul 结构，也不要回到旧的 pending_updates 主路径。
```

如果你要先把正式知识采纳的结构化输入固定下来，建议先读 `R2` 的 canonical contract：

```text
先阅读 AGENTS.md、automation_blueprint.md、codex_review_and_finalization_runbook.md、knowledge_adoption_delta_contract.md、financial-analyzer/references/open_record_protocol.md，以及 financial-analyzer/scripts/write_knowledge_adoption.py、rollback_knowledge_adoption.py、show_knowledge_adoption.py。当前聚焦 R2：知识采纳 delta 契约。请把章节级正式写入所需的 delta schema、adoption_id、logged_at、result、审计键、回滚约束和校验规则落成仓库文档，并确保它能被后续 Codex 线程直接消费；不要改 Soul 结构，也不要重新引入 pending_updates 作为主学习路径。
```

如果你要先做最小真实演练，建议开 `R3`：

```text
先阅读 AGENTS.md、automation_blueprint.md、codex_review_and_finalization_runbook.md、knowledge_adoption_delta_contract.md、financial-analyzer/SKILL.md，以及最近一次 P5 仿真结果。当前聚焦 R3：1-2 个完整案例的 scaffold -> review -> adopt -> formalization 演练。请选取最小但真实的案例，跑通章节复核、delta 生成、adoption log 写入、rollback 预案和正式产物收口，并把缺口写成可执行清单；不要扩到 10 案批量，也不要改回旧的 review bundle 主链路。
```

如果你已经完成 R1/R2/R3，下一步再开 `P6`：

```text
先阅读 AGENTS.md、automation_blueprint.md、production_execution_runbook.md，以及最近一次 R3 演练结果。当前聚焦生产化 P6：Go-Live Checklist。请基于现有系统的真实能力边界，整理一份正式投入使用前的 go-live checklist，至少覆盖 skill 安装校验、runtime 配置校验、registry 状态、批处理成功率门槛、人工抽检点、scaffold 与正式产物的交接边界、知识写入审核边界、失败重跑策略、回滚策略和“哪些问题出现时必须停止上线”。请把结果落成仓库文档。
```

当前最稳的组合是：主线程先做 `R1`，然后 `R2`，再做 `R3`，最后才进入 `P6`。
