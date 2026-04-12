#!/usr/bin/env node
/**
 * Generate SKILL.md files from BondClaw prompt library JSON packs.
 * Run from src/ directory: node scripts/generate-bondclaw-skills.mjs
 *
 * Reads: ../prompt-library/packs/{role}/{workflow}.json
 * Writes: src/process/resources/skills/bondclaw-workflows/{role}-{workflow}/SKILL.md
 */
import { readFileSync, writeFileSync, mkdirSync, readdirSync, existsSync } from 'fs';
import { join, basename } from 'path';

const PACKS_DIR = join(import.meta.dirname, '..', '..', 'prompt-library', 'packs');
const OUTPUT_DIR = join(import.meta.dirname, '..', 'src', 'process', 'resources', 'skills', 'bondclaw-workflows');

const ROLE_DISPLAY_NAMES = {
  macro: '宏观研究员',
  rates: '利率研究员',
  credit: '信用研究员',
  convertibles: '转债研究员',
  'multi-asset': '多资产研究员',
  'fund-manager': '固收基金经理',
  trader: '固收交易员',
};

const ROLE_DESCRIPTIONS = {
  macro: '宏观经济分析，包括资金面、政策预期、海外市场',
  rates: '利率曲线分析，包括期限利差、招投标、曲线定位',
  credit: '信用主体分析，包括发行人深挖、财报复核、条款审查',
  convertibles: '可转债分析，包括双低筛选、Delta敞口、Gamma波段',
  'multi-asset': '多资产配置，包括跨资产估值、体制轮动、相关性变化',
  'fund-manager': '组合管理，包括晨会打包、风险审查、策略更新',
  trader: '交易执行，包括执行记录、头寸对账、收盘检查',
};

function readJson(filePath) {
  try {
    return JSON.parse(readFileSync(filePath, 'utf-8'));
  } catch {
    return null;
  }
}

function generateSkillMd(pack) {
  const { role, workflow, prompt_template, input_schema, output_format, qa_checklist, sample_case } = pack;
  const skillName = `bondclaw-${role}-${workflow}`;
  const displayName = ROLE_DISPLAY_NAMES[role] || role;
  const roleDesc = ROLE_DESCRIPTIONS[role] || '';

  // Build input fields description
  let inputFields = '';
  if (input_schema?.properties) {
    const required = input_schema.required || [];
    inputFields = Object.entries(input_schema.properties)
      .map(([key, val]) => `- **${key}** (${required.includes(key) ? '必填' : '可选'}): ${val.type}`)
      .join('\n');
  }

  // Build QA checklist
  const qaList = (qa_checklist || []).map((item) => `- [ ] ${item}`).join('\n');

  // Build sample case
  let sampleStr = '';
  if (sample_case) {
    sampleStr = Object.entries(sample_case)
      .map(([k, v]) => `- ${k}: ${JSON.stringify(v)}`)
      .join('\n');
  }

  return `---
name: ${skillName}
description: "BondClaw ${displayName}工作流: ${workflow}. ${roleDesc}. 输入参数后生成标准化分析报告。"
---

# ${displayName} — ${workflow}

## 角色说明
${roleDesc}

## Prompt 模板

${prompt_template}

## 输入要求

${inputFields || '无需额外输入参数'}

## 输出格式

${output_format}

## 示例

${sampleStr || '无示例'}

## 质量检查清单

${qaList || '无特定检查项'}
`;
}

function main() {
  if (!existsSync(PACKS_DIR)) {
    console.error(`[generate-bondclaw-skills] Packs directory not found: ${PACKS_DIR}`);
    process.exit(1);
  }

  const roles = readdirSync(PACKS_DIR, { withFileTypes: true })
    .filter((d) => d.isDirectory())
    .map((d) => d.name);

  let generated = 0;
  let skipped = 0;

  for (const role of roles) {
    const roleDir = join(PACKS_DIR, role);
    const files = readdirSync(roleDir).filter((f) => f.endsWith('.json') && f !== 'manifest.json');

    for (const file of files) {
      const workflow = basename(file, '.json');
      const pack = readJson(join(roleDir, file));
      if (!pack) {
        skipped++;
        continue;
      }

      const skillName = `${role}-${workflow}`;
      const outputDir = join(OUTPUT_DIR, skillName);
      const outputFile = join(outputDir, 'SKILL.md');

      mkdirSync(outputDir, { recursive: true });
      writeFileSync(outputFile, generateSkillMd(pack), 'utf-8');
      generated++;
    }
  }

  console.log(`[generate-bondclaw-skills] Generated ${generated} skills, skipped ${skipped}`);
}

main();
