#!/usr/bin/env node

import fs from 'node:fs';
import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, '..');
const nodeCommand = process.execPath;
const bunCommand = process.platform === 'win32' ? 'bun.exe' : 'bun';
const bunxCommand = process.platform === 'win32' ? 'bunx.exe' : 'bunx';
const npmCliPath =
  process.platform === 'win32'
    ? path.join(path.dirname(process.execPath), 'node_modules', 'npm', 'bin', 'npm-cli.js')
    : 'npm';

function npmBuildEnv(extra = {}) {
  return {
    ...extra,
    BONDCLAW_GITHUB_OWNER: process.env.BONDCLAW_GITHUB_OWNER || 'mmaaaa1a',
    BONDCLAW_GITHUB_REPO: process.env.BONDCLAW_GITHUB_REPO || 'bondclaw',
    ELECTRON_MIRROR: 'https://registry.npmmirror.com/-/binary/electron/',
    npm_config_electron_mirror: 'https://registry.npmmirror.com/-/binary/electron/',
    ELECTRON_BUILDER_BINARIES_MIRROR:
      process.env.ELECTRON_BUILDER_BINARIES_MIRROR || 'https://cdn.npmmirror.com/binaries/electron-builder-binaries/',
    NPM_CONFIG_ELECTRON_BUILDER_BINARIES_MIRROR:
      process.env.NPM_CONFIG_ELECTRON_BUILDER_BINARIES_MIRROR ||
      'https://cdn.npmmirror.com/binaries/electron-builder-binaries/',
    MSVS_VERSION: '2022',
    GYP_MSVS_VERSION: '2022',
    npm_config_msvs_version: '2022',
  };
}

function readPackageJson() {
  return JSON.parse(fs.readFileSync(path.join(rootDir, 'package.json'), 'utf8'));
}

function stripVersionPrefix(version) {
  return String(version || '')
    .replace(/^[^0-9]*/, '')
    .replace(/[\^~]/g, '');
}

function run(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: rootDir,
    env: { ...process.env, ...(options.env ?? {}) },
    encoding: 'utf8',
    stdio: options.stdio ?? 'inherit',
    shell: false,
  });
  if (result.error) {
    throw result.error;
  }
  if (typeof result.status === 'number' && result.status !== 0) {
    process.exit(result.status);
  }
  return result;
}

function runCapture(command, args, options = {}) {
  const result = spawnSync(command, args, {
    cwd: rootDir,
    env: { ...process.env, ...(options.env ?? {}) },
    encoding: 'utf8',
    stdio: ['ignore', 'pipe', 'pipe'],
    shell: false,
  });
  if (result.error) {
    throw result.error;
  }
  if (typeof result.status === 'number' && result.status !== 0) {
    const stderr = (result.stderr || '').trim();
    const stdout = (result.stdout || '').trim();
    throw new Error(stderr || stdout || `${command} exited with ${result.status}`);
  }
  return (result.stdout || '').trim();
}

function log(line = '') {
  process.stdout.write(`${line}\n`);
}

function fail(message) {
  log(message);
  process.exit(1);
}

function electronVersion() {
  const pkg = readPackageJson();
  return stripVersionPrefix(pkg.devDependencies?.electron || pkg.dependencies?.electron || '');
}

function nodeMajorVersion() {
  return Number.parseInt(process.versions.node.split('.')[0] || '0', 10);
}

function ensureNodeModules() {
  const nodeModules = path.join(rootDir, 'node_modules');
  if (fs.existsSync(nodeModules)) {
    return;
  }
  run(nodeCommand, [npmCliPath, 'install', '--no-audit', '--no-fund'], { env: npmBuildEnv() });
}

function preflight() {
  const failed = [];
  log('==========================================');
  log('  AionUI Build Preflight Check');
  log('==========================================');
  log('');

  log('[1/6] Node.js...');
  if (nodeMajorVersion() >= 22) {
    log(`  OK  Node.js v${process.versions.node}`);
  } else {
    log(`  WARN  Node.js v${process.versions.node} (recommend >= 22)`);
  }

  log('[2/6] bun...');
  try {
    const bunVer = runCapture(bunCommand, ['--version']);
    log(`  OK  bun ${bunVer}`);
  } catch {
    log('  FAIL  bun not found');
    failed.push('bun');
  }

  log('[3/6] Python (for native modules)...');
  try {
    const pythonVer = runCapture('python', ['--version']);
    log(`  OK  ${pythonVer}`);
  } catch {
    log('  WARN  Python not found (needed for native module compilation)');
  }

  log('[4/6] Dependencies (node_modules)...');
  if (fs.existsSync(path.join(rootDir, 'node_modules'))) {
    log('  OK  node_modules exists');
  } else {
    log('  WARN  node_modules missing - running: npm install');
    run(nodeCommand, [npmCliPath, 'install', '--no-audit', '--no-fund'], { env: npmBuildEnv() });
    if (fs.existsSync(path.join(rootDir, 'node_modules'))) {
      log('  OK  node_modules installed');
    } else {
      log('  FAIL  Failed to install dependencies');
      failed.push('node_modules');
    }
  }

  log('[5/6] Native modules (better-sqlite3)...');
  const sqliteNode = path.join(rootDir, 'node_modules/better-sqlite3/build/Release/better_sqlite3.node');
  const sqlitePrebuilds = path.join(rootDir, 'node_modules/better-sqlite3/prebuilds');
  if (fs.existsSync(sqliteNode) || fs.existsSync(sqlitePrebuilds)) {
    log('  OK  better-sqlite3 native module found');
  } else {
    log('  WARN  better-sqlite3 native binary missing - run: just rebuild-native');
  }

  log('[6/6] Electron version...');
  try {
    log(`  OK  Electron ${electronVersion()}`);
  } catch {
    log('  FAIL  Cannot read Electron version');
    failed.push('electron');
  }

  log('');
  log('==========================================');
  if (failed.length > 0) {
    log('  PREFLIGHT FAILED');
    log('==========================================');
    process.exit(1);
  }
  log('  PREFLIGHT PASSED');
  log('==========================================');
}

function info() {
  log('AionUI Build Environment');
  log('========================');
  log(`Node:     v${process.versions.node}`);
  try {
    log(`bun:      ${runCapture(bunCommand, ['--version'])}`);
  } catch {
    log('bun:      not found');
  }
  log(`App:      v${readPackageJson().version}`);
  log(`Electron: ${electronVersion()}`);
  try {
    log(`Branch:   ${runCapture('git', ['branch', '--show-current'])}`);
  } catch {
    log('Branch:   unknown');
  }
  try {
    log(`Commit:   ${runCapture('git', ['rev-parse', '--short', 'HEAD'])}`);
  } catch {
    log('Commit:   unknown');
  }
}

function rebuildNative() {
  log('==========================================');
  log(`Rebuilding native modules for Electron ${electronVersion()}`);
  log('==========================================');
  log('');
  log('[Step 1] electron-rebuild...');
  run(bunxCommand, ['electron-rebuild', '-f', '-w', 'better-sqlite3']);
  log('  OK  electron-rebuild completed');
  log('');
  log('[Verify] Checking native modules...');
  const sqliteNode = path.join(rootDir, 'node_modules/better-sqlite3/build/Release/better_sqlite3.node');
  const sqlitePrebuilds = path.join(rootDir, 'node_modules/better-sqlite3/prebuilds');
  if (fs.existsSync(sqliteNode)) {
    const sizeMb = Math.round((fs.statSync(sqliteNode).size / (1024 * 1024)) * 10) / 10;
    log(`  OK  better-sqlite3 (${sizeMb} MB)`);
  } else if (fs.existsSync(sqlitePrebuilds)) {
    log('  OK  better-sqlite3 (prebuilds)');
  } else {
    fail('  FAIL  better-sqlite3 native module not found');
  }
  log('');
  log('  All native modules verified');
}

function verifyNative() {
  log('Verifying native modules can be loaded...');
  run(
    nodeCommand,
    [
      '-e',
      "try { require('better-sqlite3'); console.log('OK'); } catch (e) { console.log('FAIL: ' + e.message); process.exit(1); }",
    ],
    {
      stdio: 'pipe',
    }
  );
  log('  OK  better-sqlite3 loads correctly');
  log('All native modules verified and loadable.');
}

function buildWithBuilder(args, extraEnv = {}) {
  const env = {
    NODE_OPTIONS: '--max-old-space-size=8192',
    npm_config_runtime: 'electron',
    npm_config_target: electronVersion(),
    npm_config_disturl: 'https://electronjs.org/headers',
    ...extraEnv,
  };
  run(nodeCommand, ['scripts/build-with-builder.js', ...args], { env });
}

function runElectronBuilder(extraArgs = [], extraEnv = {}) {
  run(bunxCommand, ['electron-builder', '--config', 'electron-builder.yml', '--publish', 'never', ...extraArgs], {
    env: npmBuildEnv({
      NODE_OPTIONS: '--max-old-space-size=8192',
      ...extraEnv,
    }),
  });
}

function buildWinX64() {
  ensureNodeModules();
  run(bunCommand, ['run', 'package'], { env: npmBuildEnv({ NODE_OPTIONS: '--max-old-space-size=8192' }) });
  runElectronBuilder(['--win', '--x64'], {
    npm_config_arch: 'x64',
    npm_config_target_arch: 'x64',
  });
}

function buildWinArm64() {
  ensureNodeModules();
  run(bunCommand, ['run', 'package'], { env: npmBuildEnv({ NODE_OPTIONS: '--max-old-space-size=8192' }) });
  runElectronBuilder(['--win', '--arm64'], {
    npm_config_arch: 'arm64',
    npm_config_target_arch: 'arm64',
  });
}

function buildWin() {
  buildWinX64();
}

function buildMacArm64() {
  ensureNodeModules();
  run(bunCommand, ['run', 'package'], { env: npmBuildEnv({ NODE_OPTIONS: '--max-old-space-size=8192' }) });
  runElectronBuilder(['--mac', '--arm64']);
}

function buildMacX64() {
  ensureNodeModules();
  run(bunCommand, ['run', 'package'], { env: npmBuildEnv({ NODE_OPTIONS: '--max-old-space-size=8192' }) });
  runElectronBuilder(['--mac', '--x64']);
}

function buildMac() {
  ensureNodeModules();
  buildMacX64();
}

function buildLinux() {
  ensureNodeModules();
  run(bunCommand, ['run', 'package'], { env: npmBuildEnv({ NODE_OPTIONS: '--max-old-space-size=8192' }) });
  runElectronBuilder(['--linux']);
}

function buildWinAuto() {
  buildWin();
}

function clean() {
  fs.rmSync(path.join(rootDir, 'out'), { recursive: true, force: true });
  fs.rmSync(path.join(rootDir, 'dist'), { recursive: true, force: true });
  log('Build artifacts cleaned.');
}

function cleanAll() {
  clean();
  fs.rmSync(path.join(rootDir, 'node_modules'), { recursive: true, force: true });
  log('Full clean complete. Run: just setup');
}

function listArtifacts() {
  const outDir = path.join(rootDir, 'out');
  if (!fs.existsSync(outDir)) {
    log('No build output found. Run: just build');
    return;
  }
  const allowed = new Set(['.exe', '.msi', '.dmg', '.deb', '.appimage', '.zip']);
  const stack = [outDir];
  let found = false;
  while (stack.length > 0) {
    const current = stack.pop();
    for (const entry of fs.readdirSync(current, { withFileTypes: true })) {
      const fullPath = path.join(current, entry.name);
      if (entry.isDirectory()) {
        stack.push(fullPath);
        continue;
      }
      const ext = path.extname(entry.name).toLowerCase();
      if (allowed.has(ext)) {
        found = true;
        const size = Math.round((fs.statSync(fullPath).size / (1024 * 1024)) * 10) / 10;
        log(`  ${entry.name}  (${size} MB)`);
      }
    }
  }
  if (!found) {
    log('No build output found. Run: just build');
  }
}

const command = process.argv[2];

switch (command) {
  case 'preflight':
    preflight();
    break;
  case 'info':
    info();
    break;
  case 'rebuild-native':
    rebuildNative();
    break;
  case 'verify-native':
    verifyNative();
    break;
  case 'build-win-x64':
    buildWinX64();
    break;
  case 'build-win-arm64':
    buildWinArm64();
    break;
  case 'build-win':
    buildWinAuto();
    break;
  case 'build-mac-arm64':
    buildMacArm64();
    break;
  case 'build-mac-x64':
    buildMacX64();
    break;
  case 'build-mac':
    buildMac();
    break;
  case 'build-linux':
    buildLinux();
    break;
  case 'clean':
    clean();
    break;
  case 'clean-all':
    cleanAll();
    break;
  case 'list-artifacts':
    listArtifacts();
    break;
  default:
    fail(`Unknown just-tools command: ${command || '<empty>'}`);
}
