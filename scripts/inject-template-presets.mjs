/**
 * Inject category: 'general' into existing presets and append template presets.
 * Usage: node scripts/inject-template-presets.mjs
 */
import { readFileSync, writeFileSync } from 'fs';
import { resolve, dirname } from 'path';
import { fileURLToPath } from 'url';

const __dirname = dirname(fileURLToPath(import.meta.url));
const PRESETS_FILE = resolve(__dirname, '..', 'src', 'src', 'common', 'config', 'presets', 'assistantPresets.ts');

let content = readFileSync(PRESETS_FILE, 'utf-8');

// Step 1: Add category: 'general' to existing presets that don't have a category
// Each existing preset has a pattern like:
//   avatar: 'xxx',
//   presetAgentType: 'xxx',
// We insert category after avatar, before presetAgentType
// But only for presets that DON'T already have a category

// Strategy: Find all preset entries and add category before 'presetAgentType' if missing
// Since the template presets already have 'category:', we only add to existing ones

const existingIds = [
  'financial-analysis', 'word-creator', 'ppt-creator', 'excel-creator',
  'morph-ppt', 'pitch-deck-creator', 'dashboard-creator', 'academic-paper',
  'financial-model-creator', 'star-office-helper', 'openclaw-setup', 'cowork',
  'game-3d', 'ui-ux-pro-max', 'planning-with-files', 'human-3-coach',
  'social-job-publisher', 'moltbook', 'beautiful-mermaid',
];

for (const id of existingIds) {
  // Find the preset entry and add category after avatar
  const pattern = new RegExp(
    `(id: '${id.replace(/[.*+?^${}()|[\]\\]/g, '\\$&')}',\\s*avatar: '[^']*',)\\s*(\\n\\s*presetAgentType:)`,
    's'
  );
  content = content.replace(pattern, `$1\n    category: 'general' as AssistantPresetCategory,$2`);
}

// Step 2: Read generated template presets
const PACKS_DIR = resolve(__dirname, '..', 'prompt-library', 'packs');
const ROLE_CONFIG = {
  macro: { avatar: '🌍', category: 'macro' },
  rates: { avatar: '📈', category: 'rates' },
  credit: { avatar: '🔍', category: 'credit' },
  convertibles: { avatar: '🔄', category: 'convertibles' },
  'multi-asset': { avatar: '🎲', category: 'multi-asset' },
  'fund-manager': { avatar: '💼', category: 'fund-manager' },
  trader: { avatar: '📊', category: 'trader' },
};

function toTitleCase(str) {
  return str.split('-').map(w => w.charAt(0).toUpperCase() + w.slice(1)).join(' ');
}

function extractDesc(template) {
  const pt = template.prompt_template || '';
  const first = pt.split(/[。\n]/)[0].trim();
  if (first.length > 80) return first.slice(0, 80) + '…';
  return first || toTitleCase(template.workflow);
}

function generatePrompt(template) {
  const sample = template.sample_case || {};
  const keys = Object.keys(sample);
  if (keys.length > 0) {
    const firstKey = keys[0];
    const val = sample[firstKey];
    return `${toTitleCase(template.workflow)}: ${firstKey}=${Array.isArray(val) ? val.join(',') : val}`;
  }
  return `Run ${toTitleCase(template.workflow)} analysis`;
}

function generateZhPrompt(template) {
  const sample = template.sample_case || {};
  const keys = Object.keys(sample);
  if (keys.length > 0) {
    const firstKey = keys[0];
    const val = sample[firstKey];
    return `${firstKey}=${Array.isArray(val) ? val.join('、') : val}`;
  }
  return `执行${toTitleCase(template.workflow)}分析`;
}

const { readdirSync, existsSync } = await import('fs');
const { join } = await import('path');

let templateEntries = '';

for (const [roleId, config] of Object.entries(ROLE_CONFIG)) {
  const roleDir = join(PACKS_DIR, roleId);
  if (!existsSync(roleDir)) continue;

  let workflows = [];
  const manifestPath = join(roleDir, 'manifest.json');
  if (existsSync(manifestPath)) {
    workflows = JSON.parse(readFileSync(manifestPath, 'utf-8')).workflows || [];
  }
  if (workflows.length === 0) {
    workflows = readdirSync(roleDir)
      .filter(f => f !== 'manifest.json' && f.endsWith('.json'))
      .map(f => f.replace('.json', ''));
  }

  for (const workflow of workflows) {
    const filePath = join(roleDir, `${workflow}.json`);
    if (!existsSync(filePath)) continue;

    const template = JSON.parse(readFileSync(filePath, 'utf-8'));
    const id = `${roleId}-${workflow}`;
    const enName = toTitleCase(workflow);
    const desc = extractDesc(template);
    const nameI18n = JSON.stringify({ 'en-US': enName, 'zh-CN': enName });
    const descI18n = JSON.stringify({ 'en-US': desc, 'zh-CN': desc });
    const promptsI18n = JSON.stringify({
      'en-US': [generatePrompt(template)],
      'zh-CN': [generateZhPrompt(template)],
    });

    templateEntries += `  {
    id: '${id}',
    avatar: '${config.avatar}',
    category: '${config.category}' as AssistantPresetCategory,
    presetAgentType: 'claude',
    templatePath: 'prompt-library/packs/${roleId}/${workflow}.json',
    ruleFiles: {},
    defaultEnabledSkills: ['research-writing'],
    nameI18n: ${nameI18n},
    descriptionI18n: ${descI18n},
    promptsI18n: ${promptsI18n},
  },
`;
  }
}

// Step 3: Insert template entries before the closing ];
const insertionPoint = content.lastIndexOf('];');
const before = content.slice(0, insertionPoint);
const after = content.slice(insertionPoint);

const newContent = before + '\n  // === Template-based assistants (generated from prompt-library) ===\n' + templateEntries + after;

writeFileSync(PRESETS_FILE, newContent, 'utf-8');

// Count entries
const presetCount = (newContent.match(/id: '/g) || []).length;
console.log(`Done. Total preset entries: ${presetCount}`);
console.log(`Existing: ${existingIds.length}, Template: ${presetCount - existingIds.length}`);
