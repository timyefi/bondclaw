# 快速上手

这是一份最短路径说明。目标不是一次性学完全部项目，而是先知道项目结构、关键入口和最小运行条件。

BondClaw V1 的工作顺序是：先把 Windows 原生桌面体验、技能、Prompt、契约和 provider 目录收口，再继续补强内容和运行治理。

## 你会先接触到什么

- `financialanalysis/`：`BondClaw` 继承的核心技能与参考实现。
- `docs/`：项目级说明文档。
- `README.md`：项目入口。
- `docs/bondclaw_v1_windows_native_architecture_decision.md`：先看产品为什么必须是 Windows 原生。
- `docs/bondclaw_v1_windows_native_installation_runbook.md`：先看最终客户怎么安装和运行。
- `docs/bondclaw_v1_windows_native_validation_plan.md`：先看验证怎么做。

## 最小理解路径

1. 先看 [README.md](../README.md)，确认项目目标和许可边界。
2. 再看 [architecture.md](architecture.md)，理解采集、解析、分析和治理的层级。
3. 然后看 [contracts.md](contracts.md)，知道哪些文件是草稿，哪些文件才是正式产物。
4. 最后看 [CONTRIBUTING.md](../CONTRIBUTING.md)，确认协作方式。

## 最小运行条件

- 能读取仓库内的核心文档。
- 有可用的原始材料或中间产物。
- 如果要跑解析或分析，相关依赖和配置需要可用。

## 先不要做的事

- 不要先改分析逻辑再补文档。
- 不要把草稿误认为最终结论。
- 不要把运行态数据写回能力模块目录。

## 一次最小案例的目标

你至少要能说清楚以下四件事：

- 这个案例是什么主体、什么年份、什么材料。
- 原始文件从哪里来。
- 中间产物放在哪里。
- 哪些文件是草稿，哪些文件才算正式产物。
