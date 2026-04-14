/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * BondClaw CLI installer.
 *
 * The installer prefers bundled seed resources first, then falls back to a
 * mainland-friendly npm registry, and finally falls back to the upstream npm
 * registry. The resulting tools are installed into a current-user prefix and
 * exposed through a persistent PATH entry so they behave like real user-level
 * CLI installs.
 */

import { safeExec, safeExecFile } from './safeExec';
import { existsSync, mkdirSync, rmSync, cpSync, readFileSync, writeFileSync, chmodSync } from 'node:fs';
import os from 'node:os';
import { join, dirname } from 'node:path';
import { spawn, spawnSync } from 'child_process';
import {
  getBundledClaudePackageRoot,
  getBundledNodeDir,
  getBundledNodeExe,
  getBundledNpmCli,
} from './bundledClaudePaths';
import {
  getBondClawCliBinDir,
  getBondClawCliRoot,
  getBondClawClaudeRuntimeDir,
  getBondClawNodeRuntimeDir,
} from './bondclawCliPaths';

const DETECT_TIMEOUT_MS = 5_000;
const INSTALL_TIMEOUT_MS = 20 * 60 * 1000;
const MAX_RETRIES = 3;

const MIRROR_REGISTRIES = ['https://registry.npmmirror.com', 'https://r.cnpmjs.org'];
const OFFICIAL_REGISTRY = 'https://registry.npmjs.org';

type InstallSource = 'bundled' | 'mirror' | 'official';
type InstallPhase =
  | 'checking_node'
  | 'seeding_bundled'
  | 'installing_mirror'
  | 'installing_official'
  | 'writing_path'
  | 'verifying'
  | 'done'
  | 'error'
  | 'rollback';

interface InstallProgressEvent {
  phase: InstallPhase;
  attempt: number;
  totalAttempts: number;
  message: string;
  stdout?: string;
  source?: InstallSource;
}

interface InstallResult {
  success: boolean;
  error?: string;
  sourceUsed?: InstallSource;
  pathWritten?: boolean;
  fallbackUsed?: boolean;
}

function emitProgress(event: InstallProgressEvent): void {
  try {
    const { ipcBridge } = require('@/common') as {
      ipcBridge: { shell: { installProgress: { emit: (e: unknown) => void } } };
    };
    ipcBridge.shell.installProgress.emit(event);
  } catch {
    // IPC may not be ready during startup; progress updates are best-effort.
  }
}

function getNodeMajor(version: string): number | null {
  const match = version.trim().match(/^v?(\d+)(?:\.(\d+))?/);
  if (!match) return null;
  return Number.parseInt(match[1] || '0', 10);
}

async function checkNodeVersion(): Promise<{ ok: boolean; version?: string }> {
  const bundledNode = getBundledNodeExe();
  if (bundledNode && existsSync(bundledNode)) {
    try {
      const { stdout } = await safeExecFile(bundledNode, ['--version'], { timeout: DETECT_TIMEOUT_MS });
      const major = getNodeMajor(stdout);
      if (major !== null && major >= 18) {
        return { ok: true, version: stdout.trim() };
      }
      return { ok: false, version: stdout.trim() };
    } catch {
      // fall through to system node
    }
  }

  try {
    const { stdout } = await safeExec('node --version', { timeout: DETECT_TIMEOUT_MS });
    const major = getNodeMajor(stdout);
    if (major !== null && major >= 18) {
      return { ok: true, version: stdout.trim() };
    }
    return { ok: false, version: stdout.trim() };
  } catch {
    return { ok: false };
  }
}

function getBundledNodeSourceDir(): string | null {
  const dir = getBundledNodeDir();
  if (!dir) return null;
  const nodeExe = join(dir, process.platform === 'win32' ? 'node.exe' : 'bin/node');
  const npmCli = join(dir, 'node_modules', 'npm', 'bin', 'npm-cli.js');
  return existsSync(nodeExe) && existsSync(npmCli) ? dir : null;
}

function getBundledClaudeSourceDir(): string | null {
  const dir = getBundledClaudePackageRoot();
  if (!dir) return null;
  const claudeCli = join(dir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');
  return existsSync(claudeCli) ? dir : null;
}

function makeDir(dir: string): void {
  mkdirSync(dir, { recursive: true });
}

function removeDir(dir: string): void {
  rmSync(dir, { recursive: true, force: true });
}

function rollbackInstall(): void {
  removeDir(getBondClawCliRoot());
  if (process.platform === 'win32') {
    removeUserRegistryPathEntry(getBondClawCliBinDir());
  }
}

function copyDirectory(src: string, dest: string): void {
  removeDir(dest);
  cpSync(src, dest, { recursive: true, force: true, dereference: true });
}

function writeTextFile(filePath: string, content: string): void {
  makeDir(dirname(filePath));
  writeFileSync(filePath, content, 'utf8');
}

function asWindowsPath(p: string): string {
  return p.replace(/\//g, '\\');
}

function createWrappers(): void {
  const binDir = getBondClawCliBinDir();
  const nodeRuntimeDir = getBondClawNodeRuntimeDir();
  const claudeRuntimeDir = getBondClawClaudeRuntimeDir();
  const isWin = process.platform === 'win32';

  makeDir(binDir);
  makeDir(nodeRuntimeDir);
  makeDir(claudeRuntimeDir);

  if (isWin) {
    const nodeExe = asWindowsPath(join(nodeRuntimeDir, 'node.exe'));
    const npmCli = asWindowsPath(join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npm-cli.js'));
    const npxCli = asWindowsPath(join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npx-cli.js'));
    const claudeCli = asWindowsPath(
      join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')
    );

    writeTextFile(
      join(binDir, 'node.cmd'),
      `@echo off\r\n"${nodeExe}" %*\r\n`
    );
    writeTextFile(
      join(binDir, 'npm.cmd'),
      `@echo off\r\n"${nodeExe}" "${npmCli}" %*\r\n`
    );
    writeTextFile(
      join(binDir, 'npx.cmd'),
      `@echo off\r\n"${nodeExe}" "${npxCli}" %*\r\n`
    );
    writeTextFile(
      join(binDir, 'claude.cmd'),
      `@echo off\r\n"${nodeExe}" "${claudeCli}" %*\r\n`
    );

    writeTextFile(
      join(binDir, 'node.ps1'),
      `& "${join(nodeRuntimeDir, 'node.exe')}" @args\r\n`
    );
    writeTextFile(
      join(binDir, 'npm.ps1'),
      `& "${join(nodeRuntimeDir, 'node.exe')}" "${join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npm-cli.js')}" @args\r\n`
    );
    writeTextFile(
      join(binDir, 'npx.ps1'),
      `& "${join(nodeRuntimeDir, 'node.exe')}" "${join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npx-cli.js')}" @args\r\n`
    );
    writeTextFile(
      join(binDir, 'claude.ps1'),
      `& "${join(nodeRuntimeDir, 'node.exe')}" "${join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')}" @args\r\n`
    );
  } else {
    const nodeExe = join(nodeRuntimeDir, 'bin', 'node');
    const npmCli = join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npm-cli.js');
    const npxCli = join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npx-cli.js');
    const claudeCli = join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');

    writeTextFile(join(binDir, 'node'), `#!/bin/sh\nexec "${nodeExe}" "$@"\n`);
    writeTextFile(join(binDir, 'npm'), `#!/bin/sh\nexec "${nodeExe}" "${npmCli}" "$@"\n`);
    writeTextFile(join(binDir, 'npx'), `#!/bin/sh\nexec "${nodeExe}" "${npxCli}" "$@"\n`);
    writeTextFile(join(binDir, 'claude'), `#!/bin/sh\nexec "${nodeExe}" "${claudeCli}" "$@"\n`);
    for (const file of ['node', 'npm', 'npx', 'claude']) {
      try {
        chmodSync(join(binDir, file), 0o755);
      } catch {
        // best-effort on non-Windows
      }
    }
  }
}

function readCurrentPath(): string {
  return process.env.PATH || '';
}

function normalizePathList(value: string): string[] {
  const separator = process.platform === 'win32' ? ';' : ':';
  return value
    .split(separator)
    .map((part) => part.trim())
    .filter(Boolean);
}

/**
 * Read the current Windows user PATH from the registry (not process.env).
 * process.env.PATH is the merged system+user PATH at process start; writing it
 * back to the User key would duplicate system entries into the user PATH.
 */
function readUserRegistryPath(): string {
  const result = spawnSync(
    process.env.COMSPEC || 'cmd.exe',
    ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command',
      '[Environment]::GetEnvironmentVariable(\'Path\', \'User\')'],
    { encoding: 'utf8', stdio: ['ignore', 'pipe', 'pipe'], windowsHide: true, timeout: 10_000 }
  );
  if (result.error || typeof result.status === 'number' && result.status !== 0) {
    throw new Error(`Failed to read user PATH from registry: ${result.stderr || result.error}`);
  }
  return (result.stdout || '').trim();
}

/**
 * Remove a specific entry from the Windows user PATH in the registry.
 */
function removeUserRegistryPathEntry(entry: string): void {
  try {
    const userPath = readUserRegistryPath();
    const entryNorm = entry.toLowerCase().replace(/\/$/, '').replace(/\\$/, '');
    const parts = userPath.split(';').filter((p) => {
      const norm = p.trim().toLowerCase().replace(/\/$/, '').replace(/\\$/, '');
      return norm !== entryNorm;
    });
    const merged = parts.join(';');
    const psScript = `[Environment]::SetEnvironmentVariable('Path', ${JSON.stringify(merged)}, 'User')`;
    spawnSync(
      process.env.COMSPEC || 'cmd.exe',
      ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', psScript],
      { stdio: 'ignore', windowsHide: true, timeout: 10_000 }
    );
  } catch {
    // Best-effort cleanup — don't block rollback on PATH removal failure.
  }
}

function writeCurrentUserPathEntry(entry: string): void {
  const separator = process.platform === 'win32' ? ';' : ':';

  if (process.platform === 'win32') {
    // Read the actual user registry PATH to avoid conflating system entries.
    const userPath = readUserRegistryPath();
    const parts = normalizePathList(userPath);
    const entryNorm = entry.toLowerCase().replace(/\/$/, '').replace(/\\$/, '');
    if (parts.some((p) => p.toLowerCase().replace(/\/$/, '').replace(/\\$/, '') === entryNorm)) {
      // Already present — skip write to avoid unnecessary registry churn.
      process.env.PATH = `${entry}${separator}${readCurrentPath()}`;
      return;
    }
    const merged = [entry, ...parts].join(separator);

    const psScript = `[Environment]::SetEnvironmentVariable('Path', ${JSON.stringify(merged)}, 'User')`;
    const result = spawnSync(
      process.env.COMSPEC || 'cmd.exe',
      ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', psScript],
      { stdio: 'ignore', windowsHide: true, timeout: 10_000 }
    );
    if (result.error) {
      throw result.error;
    }
    if (typeof result.status === 'number' && result.status !== 0) {
      throw new Error(`Failed to persist user PATH (exit code ${result.status})`);
    }
  } else {
    const home = os.homedir();
    const shellProfile = process.platform === 'darwin' ? join(home, '.zprofile') : join(home, '.profile');
    const marker = '# BondClaw CLI PATH';
    const line = `${marker}\nexport PATH="${entry.replace(/"/g, '\\"')}:$PATH"\n`;
    const existing = existsSync(shellProfile) ? readFileSync(shellProfile, 'utf8') : '';
    if (!existing.includes(marker)) {
      writeTextFile(shellProfile, `${existing}${existing.endsWith('\n') || existing.length === 0 ? '' : '\n'}${line}`);
    }
  }

  process.env.PATH = `${entry}${separator}${readCurrentPath()}`;
}

function buildVerificationEnv(): NodeJS.ProcessEnv {
  const binDir = getBondClawCliBinDir();
  const separator = process.platform === 'win32' ? ';' : ':';
  const mergedPath = normalizePathList(`${binDir}${separator}${readCurrentPath()}`).join(separator);
  return {
    ...process.env,
    PATH: mergedPath,
  };
}

async function verifyInstalledTool(command: string): Promise<void> {
  const env = buildVerificationEnv();
  const isWindows = process.platform === 'win32';

  if (isWindows) {
    await safeExec(`where ${command}`, { timeout: 10_000, env });
    return;
  }

  await safeExec(`command -v ${command}`, { timeout: 10_000, env });
}

async function verifyInstallation(): Promise<void> {
  await verifyInstalledTool('node');
  await verifyInstalledTool('npm');
  await verifyInstalledTool('claude');

  const env = buildVerificationEnv();
  await safeExec('node --version', { timeout: 10_000, env });
  await safeExec('npm --version', { timeout: 10_000, env });
  await safeExec('claude --version', { timeout: 10_000, env });
}

function npmCliFromSource(source: InstallSource): string | null {
  if (source === 'bundled') {
    return getBundledNpmCli();
  }

  const localNpm = join(getBondClawNodeRuntimeDir(), 'node_modules', 'npm', 'bin', 'npm-cli.js');
  if (existsSync(localNpm)) return localNpm;

  const systemNpm = findSystemNpmCli();
  return systemNpm || getBundledNpmCli();
}

function nodeExeForNpm(source: InstallSource): string | null {
  if (source === 'bundled') {
    return getBundledNodeExe();
  }

  const localNode = process.platform === 'win32'
    ? join(getBondClawNodeRuntimeDir(), 'node.exe')
    : join(getBondClawNodeRuntimeDir(), 'bin', 'node');
  if (existsSync(localNode)) return localNode;

  const systemNode = findSystemNodeExe();
  return systemNode || getBundledNodeExe();
}

function findSystemNodeExe(): string | null {
  if (process.platform !== 'win32') {
    return 'node';
  }

  const candidates = [
    join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'node.exe'),
    join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'nodejs', 'node.exe'),
    join(process.env.LOCALAPPDATA || '', 'Programs', 'nodejs', 'node.exe'),
  ];
  for (const candidate of candidates) {
    if (candidate && existsSync(candidate)) return candidate;
  }
  return null;
}

function findSystemNpmCli(): string | null {
  if (process.platform !== 'win32') {
    return 'npm';
  }

  const candidates = [
    join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
    join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'nodejs', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
    join(process.env.LOCALAPPDATA || '', 'Programs', 'nodejs', 'node_modules', 'npm', 'bin', 'npm-cli.js'),
  ];
  for (const candidate of candidates) {
    if (candidate && existsSync(candidate)) return candidate;
  }
  return null;
}

function findSystemNodeSourceDir(): string | null {
  if (process.platform !== 'win32') {
    return null;
  }

  const candidates = [
    join(process.env.ProgramFiles || 'C:\\Program Files', 'nodejs'),
    join(process.env['ProgramFiles(x86)'] || 'C:\\Program Files (x86)', 'nodejs'),
    join(process.env.LOCALAPPDATA || '', 'Programs', 'nodejs'),
  ];

  for (const candidate of candidates) {
    const nodeExe = join(candidate, 'node.exe');
    const npmCli = join(candidate, 'node_modules', 'npm', 'bin', 'npm-cli.js');
    if (existsSync(nodeExe) && existsSync(npmCli)) {
      return candidate;
    }
  }

  return null;
}

function ensureNodeRuntimeInstalled(): void {
  if (process.platform !== 'win32') {
    return;
  }

  const nodeRuntimeDir = getBondClawNodeRuntimeDir();
  const nodeExe = process.platform === 'win32' ? join(nodeRuntimeDir, 'node.exe') : join(nodeRuntimeDir, 'bin', 'node');
  const npmCli = join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npm-cli.js');
  if (existsSync(nodeExe) && existsSync(npmCli)) {
    return;
  }

  const bundledNode = getBundledNodeSourceDir();
  if (bundledNode) {
    copyDirectory(bundledNode, nodeRuntimeDir);
    return;
  }

  const systemNode = findSystemNodeSourceDir();
  if (systemNode) {
    copyDirectory(systemNode, nodeRuntimeDir);
    return;
  }

  throw new Error('No packaged or system Node/npm runtime is available.');
}

function getPreferredRegistries(source: InstallSource): string[] {
  if (source === 'mirror') return MIRROR_REGISTRIES;
  if (source === 'official') return [OFFICIAL_REGISTRY];
  return [];
}

function spawnNpmInstall(params: {
  source: InstallSource;
  registry: string;
  attempt: number;
  totalAttempts: number;
  onOutput: (line: string) => void;
}): Promise<void> {
  const npmCli = npmCliFromSource(params.source);
  const nodeExe = nodeExeForNpm(params.source);

  if (!npmCli || !nodeExe) {
    return Promise.reject(new Error('Bundled Node/npm runtime is incomplete.'));
  }

  const claudeRuntimeDir = getBondClawClaudeRuntimeDir();
  makeDir(claudeRuntimeDir);

  return new Promise((resolve, reject) => {
    const args = [
      'install',
      '--prefix',
      claudeRuntimeDir,
      '--no-fund',
      '--no-audit',
      '--loglevel=notice',
      `--registry=${params.registry}`,
      '@anthropic-ai/claude-code',
    ];

    const child = nodeExe === 'node' && npmCli === 'npm'
      ? spawn('npm', args, {
          env: {
            ...process.env,
            PATH: buildVerificationEnv().PATH,
            npm_config_cache: join(getBondClawCliRoot(), 'cache', 'npm'),
            npm_config_yes: 'true',
            npm_config_loglevel: 'notice',
            npm_config_registry: params.registry,
          },
          shell: false,
          windowsHide: true,
          stdio: ['ignore', 'pipe', 'pipe'],
        })
      : spawn(nodeExe, [npmCli, ...args], {
          env: {
            ...process.env,
            PATH: buildVerificationEnv().PATH,
            npm_config_cache: join(getBondClawCliRoot(), 'cache', 'npm'),
            npm_config_yes: 'true',
            npm_config_loglevel: 'notice',
            npm_config_registry: params.registry,
          },
          shell: false,
          windowsHide: true,
          stdio: ['ignore', 'pipe', 'pipe'],
        });

    let lastError = '';
    child.stdout.on('data', (chunk: Buffer) => {
      for (const line of chunk.toString().split(/\r?\n/)) {
        if (!line.trim()) continue;
        params.onOutput(line.trim());
      }
    });
    child.stderr.on('data', (chunk: Buffer) => {
      lastError = chunk.toString().trim();
      if (lastError) {
        params.onOutput(lastError);
      }
    });

    const timer = setTimeout(() => {
      child.kill();
      reject(new Error(`Timeout after ${INSTALL_TIMEOUT_MS / 1000}s`));
    }, INSTALL_TIMEOUT_MS);

    child.on('error', (error) => {
      clearTimeout(timer);
      reject(error);
    });

    child.on('close', (code) => {
      clearTimeout(timer);
      if (code === 0) {
        resolve();
      } else {
        reject(new Error(lastError || `npm exited with code ${code}`));
      }
    });
  });
}

async function installFromBundledSeed(attempt: number, totalAttempts: number): Promise<InstallResult> {
  const nodeSourceDir = getBundledNodeSourceDir();
  const claudeSourceDir = getBundledClaudeSourceDir();

  if (!nodeSourceDir || !claudeSourceDir) {
    return { success: false, error: 'Bundled seed resources are incomplete.' };
  }

  emitProgress({
    phase: 'seeding_bundled',
    attempt,
    totalAttempts,
    message: 'Using bundled Node/npm and Claude Code seed resources...',
    source: 'bundled',
  });

  copyDirectory(nodeSourceDir, getBondClawNodeRuntimeDir());
  copyDirectory(claudeSourceDir, getBondClawClaudeRuntimeDir());
  createWrappers();
  writeCurrentUserPathEntry(getBondClawCliBinDir());

  emitProgress({
    phase: 'writing_path',
    attempt,
    totalAttempts,
    message: 'Writing current-user PATH entry...',
    source: 'bundled',
  });

  emitProgress({
    phase: 'verifying',
    attempt,
    totalAttempts,
    message: 'Verifying node, npm, and claude on a fresh shell path...',
    source: 'bundled',
  });

  await verifyInstallation();

  return {
    success: true,
    sourceUsed: 'bundled',
    pathWritten: true,
    fallbackUsed: false,
  };
}

async function installFromRegistry(
  source: Exclude<InstallSource, 'bundled'>,
  attempt: number,
  totalAttempts: number,
  registry: string
): Promise<InstallResult> {
  ensureNodeRuntimeInstalled();

  emitProgress({
    phase: source === 'mirror' ? 'installing_mirror' : 'installing_official',
    attempt,
    totalAttempts,
    message: `Installing Claude Code from ${registry}...`,
    source,
  });

  await spawnNpmInstall({
    source,
    registry,
    attempt,
    totalAttempts,
    onOutput: (line) => {
      emitProgress({
        phase: source === 'mirror' ? 'installing_mirror' : 'installing_official',
        attempt,
        totalAttempts,
        message: line,
        stdout: line,
        source,
      });
    },
  });

  createWrappers();
  writeCurrentUserPathEntry(getBondClawCliBinDir());
  emitProgress({
    phase: 'writing_path',
    attempt,
    totalAttempts,
    message: 'Writing current-user PATH entry...',
    source,
  });

  emitProgress({
    phase: 'verifying',
    attempt,
    totalAttempts,
    message: 'Verifying node, npm, and claude on a fresh shell path...',
    source,
  });

  await verifyInstallation();
  return {
    success: true,
    sourceUsed: source,
    pathWritten: true,
    fallbackUsed: true,
  };
}

export async function isClaudeInstalled(): Promise<boolean> {
  const env = buildVerificationEnv();
  try {
    await safeExec('node --version', { timeout: DETECT_TIMEOUT_MS, env });
    await safeExec('npm --version', { timeout: DETECT_TIMEOUT_MS, env });
    await safeExec('claude --version', { timeout: DETECT_TIMEOUT_MS, env });
    return true;
  } catch {
    return false;
  }
}

let isInstalling = false;

export async function installClaudeCode(): Promise<InstallResult> {
  if (isInstalling) {
    return { success: false, error: 'Installation is already in progress.' };
  }
  isInstalling = true;
  try {
    return await installClaudeCodeInner();
  } finally {
    isInstalling = false;
  }
}

async function installClaudeCodeInner(): Promise<InstallResult> {
  emitProgress({
    phase: 'checking_node',
    attempt: 1,
    totalAttempts: MAX_RETRIES,
    message: 'Checking Node.js runtime...',
  });

  const nodeCheck = await checkNodeVersion();
  if (!nodeCheck.ok) {
    const msg = nodeCheck.version
      ? `Node.js ${nodeCheck.version} detected. Claude Code requires Node.js 18+.`
      : 'Node.js not found. Install or bundle a compatible Node.js runtime first.';
    emitProgress({
      phase: 'error',
      attempt: 1,
      totalAttempts: MAX_RETRIES,
      message: msg,
    });
    return { success: false, error: msg };
  }

  const bundledNodeReady = getBundledNodeSourceDir() !== null;
  const bundledClaudeReady = getBundledClaudeSourceDir() !== null;

  for (let attempt = 1; attempt <= MAX_RETRIES; attempt += 1) {
    try {
      if (bundledNodeReady && bundledClaudeReady) {
        const result = await installFromBundledSeed(attempt, MAX_RETRIES);
        emitProgress({
          phase: 'done',
          attempt,
          totalAttempts: MAX_RETRIES,
          message: 'Installation complete using bundled seed resources.',
          source: 'bundled',
        });
        return result;
      }
      throw new Error('Bundled seed resources are unavailable.');
    } catch (bundledError) {
      const bundledMessage = bundledError instanceof Error ? bundledError.message : String(bundledError);
      console.warn(`[ClaudeInstaller] Bundled seed attempt ${attempt} failed: ${bundledMessage}`);
      rollbackInstall();

      const registries = getPreferredRegistries('mirror').concat(getPreferredRegistries('official'));
      for (const registry of registries) {
        try {
          const source: InstallSource = registry === OFFICIAL_REGISTRY ? 'official' : 'mirror';
          const result = await installFromRegistry(source, attempt, MAX_RETRIES, registry);
          emitProgress({
            phase: 'done',
            attempt,
            totalAttempts: MAX_RETRIES,
            message: `Installation complete using ${source} source.`,
            source,
          });
          return result;
        } catch (networkError) {
          const errorMessage = networkError instanceof Error ? networkError.message : String(networkError);
          console.warn(`[ClaudeInstaller] ${registry} failed: ${errorMessage}`);
          rollbackInstall();
          emitProgress({
            phase: 'error',
            attempt,
            totalAttempts: MAX_RETRIES,
            message: `${registry} failed: ${errorMessage}`,
            source: registry === OFFICIAL_REGISTRY ? 'official' : 'mirror',
          });
        }
      }

      if (attempt < MAX_RETRIES) {
        await new Promise((resolve) => setTimeout(resolve, 1500));
      }
    }
  }

  const error = `Failed to install Claude Code after ${MAX_RETRIES} attempts.`;
  rollbackInstall();
  emitProgress({
    phase: 'rollback',
    attempt: MAX_RETRIES,
    totalAttempts: MAX_RETRIES,
    message: error,
  });
  return { success: false, error };
}

export async function ensureClaudeInstalled(): Promise<boolean> {
  if (await isClaudeInstalled()) {
    return true;
  }

  const result = await installClaudeCode();
  return result.success;
}
