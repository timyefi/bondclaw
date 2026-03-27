# W5 知识治理审核包

## 审核摘要
- 生成时间：2026-03-17T08:16:07+08:00
- 输入案例数：3
- 输入文件数：3
- 原始候选总数：33
- 归并后审核组数：30
- 推荐状态分布：candidate=27，promoted=1，validated=2
- 候选类型分布：field_candidate=11，rule_candidate=4，topic_candidate=15
- 问题分布：quality_issue=8

## 单文件校验
- `w6_henglong`：items=9，blocking=0，quality=1
- `w6_country_garden`：items=12，blocking=0，quality=4
- `w6_hanghai`：items=12，blocking=0，quality=1

## 推荐升级为 Promoted
- `rule_candidate` / `liquidity_pressure`：cases=2，avg_confidence=0.85，action=sample_review_then_prepare_apply_bundle

## 推荐升级为 Validated
- `topic_candidate` / `其他应收款`：cases=2，action=sample_review_scope_divergence
- `topic_candidate` / `应收账款`：cases=2，action=sample_review_scope_divergence

## 需优先抽样复核
- `rule_candidate` / `liquidity_pressure`：status=promoted，priority=high，issues=-
- `field_candidate` / `#### (`：status=candidate，priority=high，issues=title_empty_after_normalization
- `field_candidate` / `受限资金`：status=candidate，priority=high，issues=title_markdown_noise
- `field_candidate` / `合计`：status=candidate，priority=high，issues=title_markdown_noise
- `field_candidate` / `根据过往违约经验及可能影响租客偿还未清余额能力的前瞻性资料，本集团按个别租户情`：status=candidate，priority=high，issues=title_too_long
- `topic_candidate` / `典型`：status=candidate，priority=high，issues=title_too_short
- `topic_candidate` / `重要`：status=candidate，priority=high，issues=title_too_short
- `field_candidate` / `代建项目`：status=candidate，priority=medium，issues=-
- `field_candidate` / `土地一级开发`：status=candidate，priority=medium，issues=-
- `field_candidate` / `坏账准备`：status=candidate，priority=medium，issues=-
- `field_candidate` / `应收政府组合`：status=candidate，priority=medium，issues=-
- `field_candidate` / `现金及现金等价物`：status=candidate，priority=medium，issues=-
- `field_candidate` / `理财产品仅`：status=candidate，priority=medium，issues=-
- `field_candidate` / `许村镇政府`：status=candidate，priority=medium，issues=-
- `rule_candidate` / `asset_impairment`：status=candidate，priority=medium，issues=-

## 审核说明
- 本轮只生成建议决议，不直接写入 `knowledge_base.json`。
- 抽样优先看 `recommended_status=promoted`、有 blocking/quality issue 的组，以及标题归一化后仍可疑的组。
- `field_candidate` 在 MVP 最高只建议到 `validated`。
