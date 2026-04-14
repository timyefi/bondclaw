#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, '..');
const targetArch = process.env.npm_config_target_arch || process.env.npm_config_arch || process.arch;
const targetNodeDir = path.join(rootDir, 'resources', 'bundled-node', `${process.platform}-${targetArch}`);
const claudeCodeDir = path.join(rootDir, 'resources', 'claude-code');

function log(message) {
  process.stdout.write(`${message}\n`);
}

function copyIfExists(source, destination) {
  if (!fs.existsSync(source)) return false;
  fs.mkdirSync(path.dirname(destination), { recursive: true });
  fs.cpSync(source, destination, { recursive: true, force: true, dereference: true });
  return true;
}

function prepareBundledNode() {
  if (process.platform !== 'win32') {
    log('[prepare-cli-resources] Skipping bundled Node seed preparation on non-Windows.');
    return;
  }

  if (targetArch !== process.arch) {
    log(`[prepare-cli-resources] Skipping bundled Node seed preparation for cross-arch target ${targetArch} from host ${process.arch}.`);
    return;
  }

  const sourceRoot = path.dirname(process.execPath);
  const sourceNodeExe = path.join(sourceRoot, 'node.exe');
  const sourceNpmDir = path.join(sourceRoot, 'node_modules', 'npm');

  if (!fs.existsSync(sourceNodeExe) || !fs.existsSync(sourceNpmDir)) {
    log(`[prepare-cli-resources] Node seed source is incomplete: ${sourceRoot}`);
    return;
  }

  fs.rmSync(targetNodeDir, { recursive: true, force: true });
  fs.mkdirSync(targetNodeDir, { recursive: true });

  const filesToCopy = [
    'node.exe',
    'npm',
    'npm.cmd',
    'npm.ps1',
    'npx',
    'npx.cmd',
    'npx.ps1',
    'corepack',
    'corepack.cmd',
    'corepack.ps1',
    'nodevars.bat',
    'install_tools.bat',
  ];

  for (const fileName of filesToCopy) {
    copyIfExists(path.join(sourceRoot, fileName), path.join(targetNodeDir, fileName));
  }

  copyIfExists(sourceNpmDir, path.join(targetNodeDir, 'node_modules', 'npm'));

  const sourceCorepackDir = path.join(sourceRoot, 'node_modules', 'corepack');
  copyIfExists(sourceCorepackDir, path.join(targetNodeDir, 'node_modules', 'corepack'));

  log(`[prepare-cli-resources] Seeded bundled Node/npm resources into ${targetNodeDir}`);
}

/**
 * Prepare the bundled Claude Code CLI seed package.
 * Runs `npm install` in resources/claude-code/ to create a pre-installed seed
 * that can be copied during the app's first-run installation, avoiding network
 * access when possible.
 */
function prepareBundledClaudeCode() {
  const claudeCliMarker = path.join(
    claudeCodeDir,
    'node_modules',
    '@anthropic-ai',
    'claude-code',
    'cli.js'
  );

  if (fs.existsSync(claudeCliMarker)) {
    log('[prepare-cli-resources] Claude Code seed already present, skipping npm install.');
    return;
  }

  log('[prepare-cli-resources] Preparing Claude Code seed package...');

  fs.rmSync(claudeCodeDir, { recursive: true, force: true });
  fs.mkdirSync(claudeCodeDir, { recursive: true });

  fs.writeFileSync(
    path.join(claudeCodeDir, 'package.json'),
    JSON.stringify({ dependencies: { '@anthropic-ai/claude-code': '*' } }, null, 2)
  );

  // Prefer mainland-friendly registry during build.
  const registry =
    process.env.npm_config_registry || 'https://registry.npmmirror.com';

  const npmCliPath = path.join(
    path.dirname(process.execPath),
    'node_modules',
    'npm',
    'bin',
    'npm-cli.js'
  );

  const result = spawnSync(
    process.execPath,
    [npmCliPath, 'install', '--production', '--no-optional', `--registry=${registry}`],
    { cwd: claudeCodeDir, stdio: 'inherit', shell: false }
  );

  if (result.error) {
    throw result.error;
  }
  if (typeof result.status === 'number' && result.status !== 0) {
    throw new Error(`npm install for Claude Code seed exited with code ${result.status}`);
  }

  if (!fs.existsSync(claudeCliMarker)) {
    throw new Error('Claude Code seed cli.js not found after npm install.');
  }

  log(`[prepare-cli-resources] Claude Code seed prepared in ${claudeCodeDir}`);
}

prepareBundledNode();
prepareBundledClaudeCode();
