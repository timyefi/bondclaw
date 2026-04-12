/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { app } from 'electron';
import * as fs from 'fs';
import * as path from 'path';
import { ipcBridge } from '@/common';
import {
  buildBondClawRuntimeSnapshot,
  getBondClawRuntimeManifestUrl,
  getBondClawRuntimeSnapshot,
  resetBondClawRuntimeSnapshot,
  setBondClawRuntimeSnapshot,
  type BondClawRuntimeSnapshot,
  type BondClawRuntimeSource,
} from '@/common/config/bondclawRuntimeState';
import type { BondClawWorkspaceQuery, BondClawWorkspaceSnapshot } from '@/common/config/bondclawWorkspaceSnapshot';
import { getBondClawReleaseManifest } from '@/common/config/bondclawReleaseManifest';

type RuntimeManifestCache = {
  manifest: ReturnType<typeof getBondClawReleaseManifest>;
  source: BondClawRuntimeSource;
  loadedAt: string;
};

const RUNTIME_CACHE_DIR = path.join(app.getPath('userData'), 'bondclaw');
const RUNTIME_CACHE_FILE = path.join(RUNTIME_CACHE_DIR, 'release-manifest.json');
const REQUEST_TIMEOUT_MS = 15000;
const FALLBACK_PROMPT_NAME_BY_ROLE: Record<string, string> = {
  macro: 'daily-brief',
  rates: 'curve-attribution',
  credit: 'issuer-deep-dive',
  convertibles: 'double-low-screening',
  'multi-asset': 'cross-asset-allocation',
  'fund-manager': 'morning-meeting-pack',
  trader: 'inventory-scan',
};

const resolveRepoRoot = (): string => {
  const envRoot = process.env.BONDCLAW_REPO_ROOT?.trim();
  const candidates = [
    envRoot,
    process.cwd(),
    path.resolve(process.cwd(), '..'),
    path.resolve(process.cwd(), '../..'),
    path.resolve(__dirname, '../../../../../'),
  ].filter((item): item is string => Boolean(item));

  for (const candidate of candidates) {
    if (fs.existsSync(path.join(candidate, 'prompt-library')) && fs.existsSync(path.join(candidate, 'src'))) {
      return candidate;
    }
  }

  return process.cwd();
};

/**
 * Resolve the directory containing prompt packs.
 * In production: looks for bundled data under the app's out/main/ directory.
 * In development: falls back to the repo root's prompt-library/.
 */
const resolvePacksDir = (): string => {
  // Production: viteStaticCopy bundles packs into out/main/bondclaw-prompts/
  const bundledPacks = path.join(__dirname, 'bondclaw-prompts');
  if (fs.existsSync(bundledPacks)) {
    return bundledPacks;
  }
  // Development: repo root prompt-library/packs/
  return path.join(resolveRepoRoot(), 'prompt-library', 'packs');
};

/**
 * Resolve the directory containing research-brain data.
 */
const resolveResearchBrainDir = (): string => {
  const bundled = path.join(__dirname, 'bondclaw-research-brain');
  if (fs.existsSync(bundled)) {
    return bundled;
  }
  return path.join(resolveRepoRoot(), 'research-brain');
};

const readJsonFile = <T>(filePath: string, fallback: T): T => {
  try {
    if (!fs.existsSync(filePath)) return fallback;
    return JSON.parse(fs.readFileSync(filePath, 'utf-8')) as T;
  } catch (error) {
    console.warn('[BondClaw] Failed to read JSON file:', filePath, error);
    return fallback;
  }
};

const listPromptRoleManifests = () => {
  const packsDir = resolvePacksDir();
  if (!fs.existsSync(packsDir)) return [];

  return fs
    .readdirSync(packsDir, { withFileTypes: true })
    .filter((item) => item.isDirectory())
    .map((item) => {
      const roleId = item.name;
      const manifestPath = path.join(packsDir, roleId, 'manifest.json');
      const manifest = readJsonFile<Record<string, any>>(manifestPath, {});
      const promptNames = fs
        .readdirSync(path.join(packsDir, roleId), { withFileTypes: true })
        .filter((entry) => entry.isFile() && entry.name.endsWith('.json') && entry.name !== 'manifest.json')
        .map((entry) => path.basename(entry.name, '.json'))
        .sort((a, b) => a.localeCompare(b));

      return {
        roleId,
        manifest,
        promptNames,
      };
    })
    .filter((item) => item.manifest && typeof item.manifest === 'object');
};

const buildPromptPack = (roleId: string, promptName: string) => {
  const promptPath = path.join(resolvePacksDir(), roleId, `${promptName}.json`);
  return readJsonFile<Record<string, any>>(promptPath, {});
};

const buildTemplateCenterSnapshot = (
  query: BondClawWorkspaceQuery,
  settings: {
    defaultRoleId: string;
    defaultPromptName: string;
    defaultProviderId: string;
  }
) => {
  const roleManifests = listPromptRoleManifests();
  const roleCards = roleManifests.map(({ roleId, manifest, promptNames }) => ({
    role_id: roleId,
    display_name: manifest.display_name || roleId,
    canonical_skill: manifest.canonical_skill || 'research-writing',
    workflow_count: Array.isArray(manifest.workflows) ? manifest.workflows.length : 0,
    sample_count: promptNames.length,
    prompt_preview: promptNames.slice(0, 4),
    prompt_count: promptNames.length,
    selected: roleId === (query.role || settings.defaultRoleId),
  }));
  const selectedRoleId = query.role || settings.defaultRoleId;
  const selectedRole = roleCards.find((item) => item.role_id === selectedRoleId) || roleCards[0] || {};
  const selectedPromptName = selectedRole.prompt_preview?.includes(settings.defaultPromptName)
    ? settings.defaultPromptName
    : selectedRole.prompt_preview?.[0] || settings.defaultPromptName;
  const selectedPromptPack =
    selectedRoleId && selectedPromptName ? buildPromptPack(selectedRoleId, selectedPromptName) : {};

  return {
    header: {
      title: 'BondClaw 模板中心',
      description: '按角色浏览模板、样例和 QA 卡，默认直达可用工作流',
      role_count: roleCards.length,
      workflow_count: roleCards.reduce((sum, card) => sum + (card.workflow_count || 0), 0),
      sample_count: roleCards.reduce((sum, card) => sum + (card.sample_count || 0), 0),
      target_workflow_count_per_role: 20,
    },
    role_cards: roleCards,
    default_context: {
      default_role_id: settings.defaultRoleId,
      default_prompt_name: settings.defaultPromptName,
      default_provider_id: settings.defaultProviderId,
      selected_role_id: selectedRoleId,
      selected_prompt_name: selectedPromptName,
    },
    selected_role: {
      role_id: selectedRoleId,
      display_name: selectedRole.display_name || selectedRoleId,
      manifest: selectedRoleId ? roleManifests.find((item) => item.roleId === selectedRoleId)?.manifest || {} : {},
      prompt_names: selectedRole.prompt_preview ? [...selectedRole.prompt_preview] : [],
      workflow_count: selectedRole.workflow_count || 0,
      sample_count: selectedRole.sample_count || 0,
    },
    selected_prompt: {
      prompt_name: selectedPromptName,
      prompt_pack: selectedPromptPack,
      prompt_error:
        selectedRoleId && selectedPromptName && !Object.keys(selectedPromptPack).length ? 'Prompt not found' : '',
    },
    recommended_actions: [
      { action_id: 'open-selected-prompt', label: '查看选中模板', kind: 'prompt' },
      { action_id: 'browse-by-role', label: '按角色浏览模板', kind: 'prompt-browser' },
      { action_id: 'open-role-manifest', label: '查看角色清单', kind: 'manifest' },
      { action_id: 'open-template-library', label: '查看当前模板', kind: 'prompt' },
      { action_id: 'open-expansion-plan', label: '查看扩展计划', kind: 'plan' },
    ],
    notes: [
      '模板中心保持本地目录优先读取',
      '每个角色先看 manifest，再看具体模板卡片',
      '后续可把 selected_prompt 直接作为执行入口',
    ],
  };
};

const buildResearchBrainSnapshot = (query: BondClawWorkspaceQuery) => {
  const researchBrainDir = resolveResearchBrainDir();
  const manifest = readJsonFile<Record<string, any>>(path.join(researchBrainDir, 'manifest.json'), {});
  const caseIndex = readJsonFile<Record<string, any>>(path.join(researchBrainDir, 'case-library', 'index.json'), {
    cases: [],
    case_count: 0,
  });
  const cases = Array.isArray(caseIndex.cases) ? caseIndex.cases : [];
  const filteredCases = cases.filter((item) => {
    if (query.role && item.prompt_role !== query.role && !(item.role_tags || []).includes(query.role)) return false;
    if (query.topic && !(item.topic_tags || []).includes(query.topic)) return false;
    return true;
  });
  const selectedCase =
    (query.caseId ? cases.find((item) => item.case_id === query.caseId) : undefined) ||
    filteredCases[0] ||
    cases[0] ||
    {};
  const promptRole = String(selectedCase.prompt_role || query.role || 'macro');
  const promptWorkflow = String(selectedCase.recommended_prompt || selectedCase.prompt_workflow || '');
  const promptPack = promptRole && promptWorkflow ? buildPromptPack(promptRole, promptWorkflow) : {};
  const promptShortcuts = selectedCase
    ? [
        {
          prompt_role: selectedCase.prompt_role,
          prompt_workflow: selectedCase.prompt_workflow,
          prompt_name: selectedCase.recommended_prompt,
          prompt_title: String(promptPack.prompt_template || '').slice(0, 48),
          output_format: promptPack.output_format,
          qa_checklist: promptPack.qa_checklist || [],
        },
      ]
    : [];
  const themeDefinitions = [
    ['macro', '宏观'],
    ['rates', '利率'],
    ['credit', '信用'],
    ['convertibles', '转债'],
    ['multi-asset', '多资产'],
    ['fund-manager', '固收基金经理'],
    ['trader', '固收交易员'],
  ] as const;
  const themeOverview = themeDefinitions.map(([themeId, displayName]) => {
    const matchingCases = cases.filter((item: Record<string, any>) => {
      const roleTags = Array.isArray(item.role_tags) ? item.role_tags : [];
      return item.prompt_role === themeId || roleTags.includes(themeId);
    });
    const matchingSources = (manifest.source_groups || []).filter((group: Record<string, any>) => {
      const roleTags = Array.isArray(group.role_tags) ? group.role_tags : [];
      return roleTags.includes(themeId);
    });
    const topicTags = Array.from(
      new Set(
        matchingCases.flatMap((item: Record<string, any>) => (Array.isArray(item.topic_tags) ? item.topic_tags : []))
      )
    ).slice(0, 4);
    const roleTags = Array.from(
      new Set(
        matchingCases.flatMap((item: Record<string, any>) => (Array.isArray(item.role_tags) ? item.role_tags : []))
      )
    );
    return {
      theme_id: themeId,
      display_name: displayName,
      case_count: matchingCases.length,
      source_group_count: matchingSources.length,
      topic_tags: topicTags,
      role_tag_count: roleTags.length,
      summary: `${matchingCases.length} 个案例，${matchingSources.length} 个来源分组`,
    };
  });

  return {
    header: {
      title: 'BondClaw 信息中心',
      description: '订阅源、案例卡、案例筛选和研究提醒都在这里集中浏览',
      source_count: manifest.source_groups?.length || 0,
      case_count: caseIndex.case_count || cases.length,
      source_group_count: (manifest.source_groups || []).length,
      source_card_count: (manifest.source_groups || []).length,
      theme_overview_count: themeOverview.length,
      case_highlight_count: filteredCases.slice(0, 3).length,
      case_detail_card_count: filteredCases.length,
      default_polling_interval: manifest.default_polling_interval || '15m',
    },
    source_groups: manifest.source_groups || [],
    source_cards: (manifest.source_groups || []).map((group: Record<string, any>) => {
      const topicTags = Array.isArray(group.topic_tags) ? group.topic_tags : [];
      const roleTags = Array.isArray(group.role_tags) ? group.role_tags : [];
      return {
        group_id: group.group_id || '',
        title: group.display_name || '',
        topic_count: topicTags.length,
        role_count: roleTags.length,
        topic_tags: topicTags.slice(0, 4),
        role_tags: roleTags.slice(0, 4),
        polling_interval: group.polling_interval || '',
        notification_policy: group.notification_policy || '',
        summary: `${topicTags.length} 个主题标签，覆盖 ${roleTags.length} 个角色标签`,
      };
    }),
    theme_overview: themeOverview,
    filters: {
      selected_role: query.role || 'macro',
      selected_topic: query.topic || '',
      selected_case_id: query.caseId || '',
      available_roles: listPromptRoleManifests().map((item) => ({
        role_id: item.roleId,
        display_name: item.manifest.display_name || item.roleId,
      })),
      available_topics: Array.from(
        new Set((manifest.source_groups || []).flatMap((group: Record<string, any>) => group.topic_tags || []))
      ),
      case_count: filteredCases.length,
    },
    case_browser: {
      entry_point: 'research-brain/case-library/index.json',
      notification_order: manifest.notification_order || [],
      cases: filteredCases,
      case_cards: filteredCases.slice(0, 6),
    },
    case_details: selectedCase
      ? {
          selected_case: selectedCase,
          visible_case_cards: filteredCases.slice(0, 6),
          case_index_path: 'research-brain/case-library/index.json',
          selected_prompt_pack: promptPack,
          selected_prompt_error:
            promptRole && promptWorkflow && !Object.keys(promptPack).length ? 'Prompt not found' : '',
          evidence_card: {
            title: selectedCase.title || '',
            summary: selectedCase.summary || '',
            source_refs: selectedCase.source_refs || [],
            evidence_hints: selectedCase.evidence_hints || [],
          },
          prompt_card: {
            title: selectedCase.recommended_prompt || '',
            workflow: selectedCase.prompt_workflow || '',
            role: selectedCase.prompt_role || '',
            prompt_template: promptPack.prompt_template || '',
            output_format: promptPack.output_format || '',
            qa_checklist: promptPack.qa_checklist || [],
          },
          action_card: {
            case_id: selectedCase.case_id || '',
            primary_action: 'open-selected-prompt',
            secondary_action: 'browse-by-role',
            recommended_prompt: selectedCase.recommended_prompt || '',
          },
        }
      : {},
    case_highlights: filteredCases.slice(0, 3).map((item: Record<string, any>) => ({
      case_id: item.case_id || '',
      title: item.title || '',
      prompt_role: item.prompt_role || '',
      prompt_workflow: item.prompt_workflow || '',
      summary: item.summary || '',
      topic_tags: item.topic_tags || [],
      role_tags: item.role_tags || [],
    })),
    prompt_shortcuts: promptShortcuts,
    recommended_actions: [
      { action_id: 'refresh-feeds', label: '刷新订阅', kind: 'subscription' },
      { action_id: 'filter-by-theme', label: '按主题筛选案例', kind: 'theme-filter' },
      { action_id: 'browse-by-role', label: '按角色浏览案例', kind: 'case-browser' },
      { action_id: 'open-selected-case', label: '查看选中案例', kind: 'case-detail' },
      { action_id: 'open-selected-prompt', label: '查看对应 Prompt', kind: 'prompt' },
      { action_id: 'open-highlighted-prompt', label: '查看高亮 Prompt', kind: 'prompt' },
      { action_id: 'open-case-library', label: '查看案例库', kind: 'case-library' },
    ],
    notes: [
      '案例卡和订阅源会走本地缓存优先',
      '筛选只是在面板层收口，不改变底层 manifest',
      '后续可把 selected_role 直接映射到 Prompt 快捷入口',
    ],
  };
};

const buildContactSnapshot = () => {
  const repoRoot = resolveRepoRoot();
  const manifest = readJsonFile<Record<string, any>>(
    path.join(repoRoot, 'financialanalysis', 'lead-capture', 'manifest.json'),
    {}
  );
  const localQueue = readJsonFile<Record<string, any>>(
    path.join(repoRoot, 'desktop-shell', 'state', 'lead-capture.json'),
    readJsonFile<Record<string, any>>(
      path.join(repoRoot, 'desktop-shell', 'state', 'lead-capture.example.json'),
      readJsonFile<Record<string, any>>(
        path.join(repoRoot, 'financialanalysis', 'lead-capture', 'queue.example.json'),
        {
          queue_count: 0,
          submissions: [],
        }
      )
    )
  );
  const submissions = Array.isArray(localQueue.submissions)
    ? localQueue.submissions
        .filter((item: unknown): item is Record<string, any> => Boolean(item) && typeof item === 'object')
        .map((submission) => {
          const receipts = submission.sink_receipts || {};
          return {
            name: submission.name || '',
            role: submission.role || '',
            delivery_status: submission.delivery_status || '',
            submitted_at: submission.submitted_at || '',
            sink_receipt_count: Object.keys(receipts).length,
            sink_receipts: receipts,
            institution: submission.institution || '',
          };
        })
    : [];

  return {
    header: {
      title: 'BondClaw 联系方式',
      description: '首个核心动作触发后收集联系方式，并本地缓存、并行投递、自动重试',
      queue_count: localQueue.queue_count || 0,
      delivery_status: (localQueue.submissions || []).map((item: Record<string, any>) => item.delivery_status),
    },
    required_fields: manifest.required_fields || [],
    delivery_order: manifest.default_delivery_order || [],
    retry_policy: manifest.retry_policy || {},
    queue_status: {
      queue_count: localQueue.queue_count || 0,
      submission_count: submissions.length,
      pending_count: (localQueue.submissions || []).filter(
        (item: Record<string, any>) => item.delivery_status !== 'delivered'
      ).length,
      source: 'desktop-shell/state/lead-capture.json',
    },
    submission_cards: submissions,
    sink_notes: [
      {
        sink: 'email',
        status: 'parallel',
        note: '用于触发自动消息通知或邮箱转发',
      },
      {
        sink: 'persistent_store',
        status: 'local-or-remote',
        note: '用于保存可查询的最小记录，不要求重量级 CRM',
      },
      {
        sink: 'archive_link',
        status: 'signed-link',
        note: '用于安全链接或第三方存储中转',
      },
    ],
    recommended_actions: [
      { action_id: 'open-lead-form', label: '填写联系方式表单', kind: 'form' },
      { action_id: 'retry-pending', label: '重试未完成投递', kind: 'retry' },
      { action_id: 'queue-demo-submission', label: '新增示例提交', kind: 'queue' },
      { action_id: 'open-queue', label: '查看本地队列', kind: 'queue' },
    ],
    notes: [
      '联系方式必须在首次核心动作前后自然触发，不做重弹窗',
      '本地队列优先于网络投递，确保断网可继续工作',
      '三路投递并行，回执记录保留在本地状态里',
    ],
  };
};

const buildSettingsSnapshot = (
  runtime: ReturnType<typeof buildBondClawRuntimeSnapshot>,
  settings: {
    defaultRoleId: string;
    defaultPromptName: string;
    defaultProviderId: string;
  }
) => {
  const distribution = runtime.manifest.distribution || {};
  const featureFlags = runtime.manifest.featureFlags || {};
  const enabledFlags = Object.entries(featureFlags)
    .filter(([, enabled]) => Boolean(enabled))
    .map(([key]) => key);
  const sourceLabel = runtime.source === 'remote' ? '远程清单' : runtime.source === 'cache' ? '本地缓存' : '内置默认';
  const manifestUrl = distribution.manifestUrl || runtime.brand.releaseNotesUrl;
  return {
    header: {
      title: 'BondClaw 设置',
      description: '品牌、升级、在线入口和运行态都在这里统一查看',
      source_label: sourceLabel,
      app_name: runtime.brand.appName,
      team_label: runtime.brand.teamLabel,
      release_version: runtime.manifest.releaseVersion || '',
      release_channel: runtime.manifest.releaseChannel || '',
      enabled_flag_count: enabledFlags.length,
    },
    summary_cards: [
      { label: '品牌来源', value: sourceLabel, hint: runtime.loadedAt },
      { label: '更新仓库', value: distribution.updateRepo || '本地 bundled', hint: manifestUrl },
      { label: '启用开关', value: `${enabledFlags.length} 个`, hint: enabledFlags.join(' · ') || '无启用开关' },
      {
        label: '默认上下文',
        value: `${settings.defaultRoleId} / ${settings.defaultPromptName}`,
        hint: settings.defaultProviderId,
      },
    ],
    brand_cards: [
      { label: '应用名称', value: runtime.brand.appName, hint: 'BondClaw 首页' },
      { label: '团队', value: runtime.brand.teamLabel, hint: runtime.brand.attributionPolicy },
      { label: '支持说明', value: runtime.brand.supportBannerCopy, hint: runtime.brand.supportRibbonCopy },
      { label: '文档入口', value: runtime.brand.docsBaseUrl, hint: '在线帮助与手册' },
    ],
    update_cards: [
      {
        label: '版本',
        value: runtime.manifest.releaseVersion || '',
        hint: runtime.manifest.releaseChannel || 'stable',
      },
      { label: '清单地址', value: manifestUrl, hint: distribution.updateRepo || '本地 bundled' },
      {
        label: '运行模式',
        value: distribution.manifestUrl ? '远程清单生效' : '本地 bundled 清单',
        hint: 'Windows 采用原生执行，Mac 继续走 POSIX 路径',
      },
      { label: '升级入口', value: runtime.brand.releaseNotesUrl, hint: '查看更新说明' },
    ],
    online_cards: [
      { label: '官网', value: runtime.brand.officialWebsite, hint: '产品主页' },
      { label: '支持页', value: runtime.brand.supportUrl, hint: '帮助与反馈' },
      { label: '文档基址', value: runtime.brand.docsBaseUrl, hint: '产品手册' },
      { label: '归属与说明', value: runtime.brand.attributionPolicy, hint: '授权与来源' },
    ],
    quick_actions: [
      { action_id: 'refresh-runtime-state', label: '刷新运行态', kind: 'runtime' },
      { action_id: 'open-release-notes', label: '查看更新说明', kind: 'release-notes' },
      { action_id: 'open-docs', label: '查看文档', kind: 'docs' },
      { action_id: 'open-official-website', label: '访问官网', kind: 'website' },
      { action_id: 'open-support-page', label: '访问支持页', kind: 'support' },
    ],
    notes: [
      '设置页保持本地优先读取与远程清单覆盖',
      '升级入口只负责查看和刷新，不打断当前工作流',
      '品牌来源、升级仓库与在线入口都从运行态统一下发',
    ],
  };
};

const buildWorkspaceSnapshot = (query: BondClawWorkspaceQuery): BondClawWorkspaceSnapshot => {
  const runtime = buildBondClawRuntimeSnapshot(getBondClawReleaseManifest(), 'bundled');
  const settings = {
    defaultRoleId: 'macro',
    defaultPromptName: FALLBACK_PROMPT_NAME_BY_ROLE.macro,
    defaultProviderId: 'zai',
  };
  const templateCenter = buildTemplateCenterSnapshot(query, settings);
  const researchBrain = buildResearchBrainSnapshot(query);
  const contact = buildContactSnapshot();
  const settingsSnapshot = buildSettingsSnapshot(runtime, settings);

  return {
    loadedAt: new Date().toISOString(),
    query,
    overview: {
      appName: runtime.brand.appName,
      teamLabel: runtime.brand.teamLabel,
      sourceCount: researchBrain.header.source_count,
      caseCount: researchBrain.header.case_count,
      sourceGroupCount: researchBrain.header.source_group_count,
      sourceCardCount: researchBrain.header.source_card_count,
      themeOverviewCount: researchBrain.header.theme_overview_count,
      caseHighlightCount: researchBrain.header.case_highlight_count,
      roleCount: templateCenter.header.role_count,
      queueCount: contact.queue_status.queue_count,
      pendingCount: contact.queue_status.pending_count,
    },
    settings: settingsSnapshot,
    templateCenter,
    researchBrain,
    contact,
  };
};

const readCache = (): RuntimeManifestCache | null => {
  try {
    if (!fs.existsSync(RUNTIME_CACHE_FILE)) return null;
    const raw = fs.readFileSync(RUNTIME_CACHE_FILE, 'utf-8');
    const parsed = JSON.parse(raw) as Partial<RuntimeManifestCache>;
    if (!parsed?.manifest) return null;
    return {
      manifest: parsed.manifest,
      source: parsed.source === 'remote' ? 'remote' : 'cache',
      loadedAt: typeof parsed.loadedAt === 'string' ? parsed.loadedAt : new Date().toISOString(),
    };
  } catch (error) {
    console.warn('[BondClaw] Failed to read runtime manifest cache:', error);
    return null;
  }
};

const writeCache = async (snapshot: BondClawRuntimeSnapshot): Promise<void> => {
  try {
    await fs.promises.mkdir(RUNTIME_CACHE_DIR, { recursive: true });
    await fs.promises.writeFile(
      RUNTIME_CACHE_FILE,
      JSON.stringify(
        {
          manifest: snapshot.manifest,
          source: snapshot.source,
          loadedAt: snapshot.loadedAt,
        },
        null,
        2
      ),
      'utf-8'
    );
  } catch (error) {
    console.warn('[BondClaw] Failed to write runtime manifest cache:', error);
  }
};

const loadRemoteManifest = async (manifestUrl: string): Promise<RuntimeManifestCache | null> => {
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), REQUEST_TIMEOUT_MS);

  try {
    const response = await fetch(manifestUrl, {
      signal: controller.signal,
      headers: {
        Accept: 'application/json',
      },
    });

    if (!response.ok) {
      throw new Error(`Manifest request failed (${response.status}): ${response.statusText}`);
    }

    const parsed = (await response.json()) as ReturnType<typeof getBondClawReleaseManifest>;
    if (!parsed || typeof parsed !== 'object' || typeof parsed.schemaVersion !== 'number') {
      throw new Error('Remote manifest payload is invalid');
    }

    return {
      manifest: parsed,
      source: 'remote',
      loadedAt: new Date().toISOString(),
    };
  } catch (error) {
    console.warn('[BondClaw] Failed to load remote runtime manifest:', error);
    return null;
  } finally {
    clearTimeout(timeoutId);
  }
};

const loadRuntimeSnapshot = async (): Promise<BondClawRuntimeSnapshot> => {
  const bundled = buildBondClawRuntimeSnapshot(getBondClawReleaseManifest(), 'bundled');
  setBondClawRuntimeSnapshot(bundled);

  const cached = readCache();
  if (cached) {
    setBondClawRuntimeSnapshot(buildBondClawRuntimeSnapshot(cached.manifest, cached.source, cached.loadedAt));
  }

  const manifestUrl = getBondClawRuntimeManifestUrl();
  if (!manifestUrl) {
    return getBondClawRuntimeSnapshot();
  }

  const remote = await loadRemoteManifest(manifestUrl);
  if (remote) {
    const remoteSnapshot = buildBondClawRuntimeSnapshot(remote.manifest, remote.source, remote.loadedAt);
    setBondClawRuntimeSnapshot(remoteSnapshot);
    await writeCache(remoteSnapshot);
    return remoteSnapshot;
  }

  return getBondClawRuntimeSnapshot();
};

export const refreshBondClawRuntimeSnapshot = async (): Promise<BondClawRuntimeSnapshot> => {
  const snapshot = await loadRuntimeSnapshot();
  ipcBridge.bondclaw.runtimeStateChanged.emit(snapshot);
  return snapshot;
};

export const initBondClawBridge = (): void => {
  ipcBridge.bondclaw.getRuntimeState.provider(async () => getBondClawRuntimeSnapshot());
  ipcBridge.bondclaw.refreshRuntimeState.provider(async () => refreshBondClawRuntimeSnapshot());
  ipcBridge.bondclaw.getWorkspaceSnapshot.provider(async (query) => buildWorkspaceSnapshot(query || {}));

  void refreshBondClawRuntimeSnapshot().catch((error) => {
    console.warn('[BondClaw] Runtime manifest refresh failed:', error);
    resetBondClawRuntimeSnapshot();
  });
};
