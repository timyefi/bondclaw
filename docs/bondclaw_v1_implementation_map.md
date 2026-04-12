# BondClaw V1 发布前实施地图

这份地图回答三个问题：

1. 先改哪些文件
2. 先建哪些目录
3. 先补哪些 JSON / MD 契约

## 第一阶段：先落文档主干

先修改这些文件：

- `README.md`
- `docs/README.md`
- `docs/architecture.md`
- `docs/quickstart.md`
- `docs/contracts.md`
- `LICENSE`

先新增这两个文档：

- `docs/bondclaw_v1_implementation_map.md`
- `docs/bondclaw_v1_product_contracts.md`

## 第二阶段：先建目录

先建这些目录：

- `financialanalysis/research-writing/`
- `financialanalysis/contracts/`
- `financialanalysis/prompt-library/`
- `financialanalysis/provider-registry/`
- `financialanalysis/research-brain/`
- `financialanalysis/lead-capture/`
- `desktop-shell/`

目录用途：

- `research-writing/`：统一研报写作风格技能
- `contracts/`：放产品契约和 JSON 模板
- `prompt-library/`：放角色 Prompt 卡片与示例
- `provider-registry/`：放供应商与 coding plan 预设
- `research-brain/`：放 RSS / 订阅 / 去重 / 标签契约
- `lead-capture/`：放联系方式字段、回执和缓存契约
- `desktop-shell/`：放桌面壳 bridge、launch helper 和 shell contract
- `desktop-shell/state/`：放本地 settings 示例和状态模板
- `desktop-shell/home/`：放首页面板模型
- `desktop-shell/prompt_center/`：放模板中心面板模型
- `desktop-shell/research_brain/`：放信息中心面板模型
- `desktop-shell/lead_capture/`：放联系方式面板模型
- `desktop-shell/pages/`：放页面清单和导航模型
- `desktop-shell/settings/`：放设置页模型

## 第三阶段：先补契约

优先补这几类契约：

- `BrandingConfig`
- `ExecutionShell`
- `ProviderProfile`
- `PromptPack`
- `SkillPackManifest`
- `FeedSource`
- `LeadSubmission`

推荐写法：

- 先用 `MD` 写字段定义和行为边界
- 再用 `JSON` 给出模板和默认值
- 最后再让实现文件读取这些模板

## 第四阶段：先补技能

优先补这几个技能：

- `financialanalysis`
- `chinamoney`
- `mineru`
- `research-writing`

随后再扩：

- 固收研究模板中心
- 研究订阅技能
- 联系方式和推送辅助技能

## 第五阶段：先补运行约束

必须先定下来的运行约束：

- 默认执行环境是 Windows 原生语义
- Windows 直接使用原生执行路径
- Mac 仅作为内部开发参考环境
- Windows 打包和 installer 验证前置

## 建议的开发顺序

1. 先把品牌、文档和契约统一
2. 再补 `research-writing` 和 Prompt 目录
3. 再补 provider registry
4. 再补模板中心、信息中心和联系方式
5. 最后再接桌面壳和未来 Windows 包装
