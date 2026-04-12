# BondClaw

`BondClaw` 是一个面向专业固收投研人员的开放项目。

整个项目的核心思路是“工程化研究”。

过去我们知道，在 AI 领域，目前应用最广、应用价值发挥率最高的就是编程领域。实际上，编程之所以能很好地发挥 AI 的效用，是因为它是数字化的，整个过程高度可工程化。由此可以衍生出一个思路：任何一项深度专业的工作，要让 AI 发挥更大价值的前提，就是让工作本身更好地用工程化架构来重构。

研究工作本身其实已经具有高度工程化的潜力。我们整个流程从信息和数据的收集整理、分析框架的搭建，到基于框架的分析，以及持续的经验知识库累积循环，最后到输出展示、反馈、再循环的积累提升过程。

整个研究过程如何赋能并体现为实际投资价值，核心点在于研究需要做成“可复现、可回溯、可回测”。如果你能将研究工作工程化，就能将从研究到投资的整个价值链条搭建得非常清晰，这也是我们构建这个项目的出发点。

在过去的使用过程中我发现，相比于市场上最近出现的 OpenClaude 这种工具，编程领域中一些更专业化的工具，在应对深度专业工作时的价值远比 OpenClaude 这种架构更为强大。OpenClaude 之所以能火，核心原因在于它面向的是更广大的人群，做得更通俗。但实际上，专业研究人员需要的是更为工程化的编程工具。

问题在于，很多研究人员并不具备代码基础，很难直接安装和使用这些专业工具。所以我们的思路是：借鉴 OpenClaude 在使用体验上的优势，构建了一个 BoundClaude。它与 OpenClaude 最大的差异在于两点：

1. 底座不同：它的底座不是 OpenClaude，而是那些专业的代码工具，是彻底代码化、编程化、工程化的。
2. 内嵌经验：它内嵌了很多资深研究员过去十几年积累下来的工作流程，并将其转化为特定的 Skill。

我们将这种从研究到投资的工程化探索思路和认知，体现在了项目设计的方方面面，因此能带来相比市场其他工具不一样的体验。

它不是单点工具，而是一套从信息收集、文档解析、附注优先分析，到结构化输出、知识沉淀、订阅分发和无代码工作流编排的协作底座。

当前 V1 的开发原则是：

- Windows 原生优先，客户安装后不要求额外的 Linux 发行版或终端环境。
- 所有客户可见流程统一按 Windows 桌面应用设计。
- 技能、Prompt、研究订阅和联系方式契约先定清楚，再接桌面 UI。
- 桌面 UI 优先复用 `vendor/AionUi/` 的成熟基座，并在其上做 BondClaw 品牌与升级配置。

## 项目定位

这个项目围绕债券发行主体研究展开，核心关注的是：

- 主体是谁。
- 财务结构怎样。
- 债务压力在哪里。
- 现金是否够用。
- 条款是否有保护。
- 风险是否已经显性化。

项目希望把这些问题放进同一条链路里，而不是拆成互相割裂的脚本、表格和临时结论。

## 基础来源

`BondClaw` 在方法论和技能底座上，直接建立在 `FinancialAnalysis` 的核心能力之上。

`FinancialAnalysis` 已经证明了这条路线的可行性：采集、解析、附注定位、分析底稿和结构化结果都已经有了可参考的实践。`BondClaw` 的工作不是重新发明这一套，而是把它整理成更开放、更清晰、更适合持续协作的项目形态。

## 当前重点

当前优先级最高的方向有五个：

1. 补强信息收集层，继续扩展公开数据来源。
2. 完善文档解析和附注优先分析链路。
3. 让工作底稿、报告和结构化输出更稳定、更可复核。
4. 把知识沉淀、回滚和治理边界写清楚。
5. 把桌面壳、Windows 原生执行、供应商接入和 Prompt 卡片化落成产品契约。

## AionUi 基座

`vendor/AionUi/` 已作为桌面壳基座拉入仓库，后续 BondClaw 的桌面程序会优先在这套工程上迭代，而不是重新从零开始搭 Electron 壳。

BondClaw 的集中品牌配置与在线升级口径已经开始落地：

- 品牌主配置放在 `vendor/AionUi/src/common/config/bondclaw-brand.json`
- release manifest 放在 `vendor/AionUi/src/common/config/bondclaw-release-manifest.example.json`
- 运行时状态与远程刷新逻辑放在 `vendor/AionUi/src/common/config/bondclawRuntimeState.ts`
- 文档站基址通过 `docsBaseUrl` 统一配置
- 顶部支持条通过 `supportBannerCopy`、`supportRibbonCopy` 和 `featureFlags.supportBanner` 统一控制
- 标题栏、首页、关于页、更新桥和打包配置都会读取这份配置
- 通过正常发布/升级时，品牌、官网、支持页、仓库地址和展示文案都可以一起更新
- deep link 协议已改为 `bondclaw://`

## 仓库结构

- `README.md`：项目首页。
- `CONTRIBUTING.md`：贡献与协作说明。
- `LICENSE`：非商业使用许可。
- `docs/`：文档索引、快速上手、架构说明、实施地图和产品契约。
- `financialanalysis/`：继承自 `FinancialAnalysis` 的核心技能与参考实现。

## 你可以先读什么

如果你是第一次接触这个仓库，建议按下面顺序阅读：

1. [docs/README.md](docs/README.md)
2. [docs/bondclaw_v1_windows_native_architecture_decision.md](docs/bondclaw_v1_windows_native_architecture_decision.md)
3. [docs/bondclaw_v1_windows_native_installation_runbook.md](docs/bondclaw_v1_windows_native_installation_runbook.md)
4. [docs/bondclaw_v1_windows_native_validation_plan.md](docs/bondclaw_v1_windows_native_validation_plan.md)
5. [docs/quickstart.md](docs/quickstart.md)
6. [docs/architecture.md](docs/architecture.md)
7. [docs/contracts.md](docs/contracts.md)
8. [CONTRIBUTING.md](CONTRIBUTING.md)

## 协作方式

这个仓库按开源项目的方式组织：

- 先读文档，再动手。
- 先做最小改动，再扩展。
- 先保留边界，再谈重构。
- 先明确草稿、正式产物和运行态的区别，再推进实现。

## 许可

本仓库仅限非商业使用。任何商业使用、转售、再许可、付费托管、商业集成都不允许，除非得到权利人事先书面许可。详见 [LICENSE](LICENSE)。
