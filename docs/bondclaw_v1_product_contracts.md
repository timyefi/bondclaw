# BondClaw V1 产品契约

这份契约只定义 V1 必须先固定的产品对象，不展开实现细节。

## BrandingConfig

```json
{
  "app_name": "BondClaw",
  "team_label": "国投固收 张亮/叶青",
  "splash_copy": "国投固收 张亮/叶青",
  "docs_base_url": "https://github.com/timyefi/bondclaw/docs",
  "support_ribbon_copy": "支持国投固收研究团队",
  "support_banner_copy": "基于 BondClaw 开源项目",
  "attribution_policy": "统一展示团队名，不在通用写作技能中显示个人姓名"
}
```

## ReleaseManifest

```json
{
  "schemaVersion": 1,
  "releaseChannel": "stable",
  "releaseVersion": "1.0.0",
  "branding": {
    "appName": "BondClaw",
    "teamLabel": "国投固收 张亮/叶青",
    "officialWebsite": "https://github.com/timyefi/bondclaw",
    "githubRepository": "https://github.com/timyefi/bondclaw",
    "releaseNotesUrl": "https://github.com/timyefi/bondclaw/releases",
    "supportUrl": "https://github.com/timyefi/bondclaw/support"
  },
  "distribution": {
    "updateRepo": "https://github.com/timyefi/bondclaw",
    "manifestUrl": "https://github.com/timyefi/bondclaw/releases/bondclaw-release-manifest.json",
    "updateHosts": [
      "github.com",
      "objects.githubusercontent.com",
      "github-releases.githubusercontent.com",
      "release-assets.githubusercontent.com"
    ]
  },
  "featureFlags": {
    "researchBrain": true,
    "leadCapture": true,
    "supportBanner": true,
    "windowsNativeExecution": true,
    "autoUpdate": true
  }
}
```

## DesktopShellContract

```json
{
  "runtime_entry": "financialanalysis/financial-analyzer/scripts/bondclaw_runtime.py",
  "runtime_bridge": "desktop-shell/bridge/runtime_client.py",
  "default_execution_mode": "native",
  "windows_execution_mode": "native",
  "forbidden_defaults": ["non-native-execution"]
}
```

## HomePanelContract

```json
{
  "panel_id": "bondclaw-home",
  "panel_title": "BondClaw Home",
  "team_label": "国投固收 张亮/叶青",
  "sections": [
    "header",
    "release_status",
    "quick_actions",
    "default_context",
    "provider_status",
    "prompt_shortcuts",
    "prompt_center",
    "research_brain",
    "lead_capture",
    "support_banner"
  ]
}
```

## PromptCenterPanelContract

```json
{
  "panel_id": "bondclaw-prompt-center",
  "panel_title": "模板中心",
  "sections": [
    "header",
    "role_cards",
    "default_context",
    "selected_role",
    "selected_prompt",
    "recommended_actions",
    "notes"
  ]
}
```

## BrandUpgradePanelContract

```json
{
  "panel_id": "brand-upgrade",
  "panel_title": "设置",
  "sections": [
    "header",
    "brand_overview",
    "release_overview",
    "support_overview",
    "feature_flags",
    "update_actions",
    "notes"
  ]
}
```

## ResearchBrainPanelContract

```json
{
  "panel_id": "bondclaw-research-brain",
  "panel_title": "信息中心",
  "sections": [
    "header",
    "source_groups",
    "source_cards",
    "theme_overview",
    "filters",
    "case_browser",
    "case_details",
    "case_highlights",
    "prompt_shortcuts",
    "recommended_actions",
    "notes"
  ]
}
```

## PageMapContract

```json
{
  "shell_id": "bondclaw-desktop-shell",
  "default_page_id": "home",
  "pages": [
    "home",
    "settings",
    "providers",
    "prompts",
    "research-brain",
    "lead-capture",
    "brand-upgrade",
    "logs",
    "about"
  ]
}
```

## NavigationContract

```json
{
  "navigation_type": "sidebar",
  "sections": ["workspace", "content", "utility"],
  "primary_actions": ["home", "settings", "providers", "prompts"],
  "secondary_actions": ["research-brain", "lead-capture", "brand-upgrade", "logs", "about"]
}
```

## SettingsPanelContract

```json
{
  "panel_id": "bondclaw-settings",
  "panel_title": "Settings",
  "sections": [
    "execution",
    "provider",
    "prompt",
    "lead_capture",
    "support_banner",
    "notifications"
  ]
}
```

## ExecutionShell

```json
{
  "mode": "native",
  "shell_family": "windows",
  "command_prefix": "",
  "path_policy": "windows-native",
  "windows_runtime_note": "Windows 原生执行"
}
```

## ProviderProfile

```json
{
  "vendor": "zai",
  "plan_kind": "coding",
  "protocol": "openai-compatible",
  "default_base_url": "https://api.z.ai/api/coding/paas/v4",
  "default_model": "",
  "key_only_wizard": true,
  "advanced_override": {
    "allow_base_url_edit": true,
    "allow_model_edit": true
  }
}
```

## PromptPack

字段：

- `id`
- `role`
- `workflow`
- `variant`
- `required_skills`
- `input_schema`
- `prompt_template`
- `output_format`
- `sample_case`
- `qa_checklist`

## SkillPackManifest

字段：

- `id`
- `role_tags`
- `input_schema`
- `artifact_types`
- `risk_level`
- `execution_prerequisites`

## FeedSource

字段：

- `source_url`
- `topic_tags`
- `role_tags`
- `polling_interval`
- `dedupe_key`
- `notification_policy`

## ResearchBrainManifest

字段：

- `schemaVersion`
- `brainName`
- `default_polling_interval`
- `supported_formats`
- `notification_order`
- `dedupe_fields`
- `source_groups`
- `case_library`

## CaseLibraryIndex

字段：

- `case_id`
- `title`
- `role_tags`
- `topic_tags`
- `prompt_role`
- `prompt_workflow`
- `recommended_prompt`
- `source_refs`
- `summary`
- `evidence_hints`

## LeadSubmission

字段：

- `name`
- `institution`
- `role`
- `email`
- `phone`
- `card_image`
- `consent_version`
- `device_id`
- `client_version`
- `submitted_at`
- `delivery_status`
- `sink_receipts`

## LeadCaptureManifest

```json
{
  "schemaVersion": 1,
  "capture_name": "BondClaw 联系方式",
  "default_delivery_order": [
    "email",
    "persistent_store",
    "archive_link"
  ]
}
```

## LeadCapturePanelContract

```json
{
  "panel_id": "bondclaw-lead-capture",
  "panel_title": "联系方式",
  "sections": [
    "header",
    "required_fields",
    "delivery_order",
    "retry_policy",
    "queue_status",
    "submission_cards",
    "sink_notes",
    "recommended_actions",
    "notes"
  ]
}
```

## Provider presets

V1 默认预置以下 coding plan 供应商：

- Z.AI
- MiniMax
- ByteDance / Volcano Ark
- Alibaba
- Tencent

默认只暴露 `key` 输入，base URL 和 model 走内置预置。高级设置才允许覆盖。

## 写作技能

统一技能名称：

- `research-writing`

兼容别名：

- `yeqing-writing`
- `zhangliang-writing`

技能要求：

- 不出现个人姓名
- 只表达研报写作风格
- 可用于宏观、利率、信用、转债和策略类写作

## 联系方式与推送

联系方式与推送采用轻量链路：

- 先本地缓存
- 再并行发送
- 最后异步重试

不引入重型自建服务器作为 V1 前置条件。
