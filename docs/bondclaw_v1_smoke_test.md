<<<<<<< HEAD
# BondClaw V1 发布前 Smoke Test

这个 smoke test 用于发版前的最后一轮快速检查。  
它不替代 Windows 真机验证，也不替代人工内容审校，但可以快速告诉我们当前首页核心能力是否还在。

## 覆盖范围

- 统一 runtime 资产校验
- 模板中心
- 信息中心
- 联系方式
- 设置 / 品牌 / 升级
- 执行命令描述是否仍然遵守抽象层

## 执行方式

在仓库根目录执行：

```bash
python3 financialanalysis/financial-analyzer/scripts/bondclaw_smoke_test.py
```

## 通过标准

- runtime 资产校验通过
- 模板中心能读到角色、工作流、样例和默认上下文
- 信息中心能读到案例、来源、主题和高亮卡
- 联系方式队列能读到提交、待重试和投递顺序
- 设置页能读到品牌、升级和在线入口
- 执行命令描述应保持 Windows 原生口径

## 说明

- 这个 smoke test 依赖当前仓库里的本地数据文件，不依赖 Windows 真机。
- 它适合在发版前、内容更新后和收尾修改后快速执行。
- 如果 smoke test 失败，优先看失败项对应的收尾清单卡片：
  - [bondclaw_v1_task_cards.md](bondclaw_v1_task_cards.md)
  - [bondclaw_v1_execution_checklist.md](bondclaw_v1_execution_checklist.md)
=======
# BondClaw V1 发布前 Smoke Test

这个 smoke test 用于发版前的最后一轮快速检查。  
它不替代 Windows 真机验证，也不替代人工内容审校，但可以快速告诉我们当前首页核心能力是否还在。

## 覆盖范围

- 统一 runtime 资产校验
- 模板中心
- 信息中心
- 联系方式
- 设置 / 品牌 / 升级
- 执行命令描述是否仍然遵守抽象层

## 执行方式

在仓库根目录执行：

```bash
python3 financialanalysis/financial-analyzer/scripts/bondclaw_smoke_test.py
```

## 通过标准

- runtime 资产校验通过
- 模板中心能读到角色、工作流、样例和默认上下文
- 信息中心能读到案例、来源、主题和高亮卡
- 联系方式队列能读到提交、待重试和投递顺序
- 设置页能读到品牌、升级和在线入口
- 执行命令描述应保持 Windows 原生口径

## 说明

- 这个 smoke test 依赖当前仓库里的本地数据文件，不依赖 Windows 真机。
- 它适合在发版前、内容更新后和收尾修改后快速执行。
- 如果 smoke test 失败，优先看失败项对应的收尾清单卡片：
  - [bondclaw_v1_task_cards.md](bondclaw_v1_task_cards.md)
  - [bondclaw_v1_execution_checklist.md](bondclaw_v1_execution_checklist.md)
>>>>>>> 1183b41 (chore: sync current project snapshot)
