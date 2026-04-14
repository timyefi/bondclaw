#!/usr/bin/env node
// @ts-check
/**
 * BondClaw CLI Deployment Script
 *
 * Standalone script run by the NSIS installer via the bundled node.exe.
 * Deploys Node.js, npm, and Claude Code to the user's system:
 *   1. Copy Node.js runtime to %LOCALAPPDATA%\BondClaw\cli\runtime\node\
 *   2. Copy Claude Code to %LOCALAPPDATA%\BondClaw\cli\runtime\claude-code\
 *   3. Generate .cmd wrappers in %LOCALAPPDATA%\BondClaw\cli\bin\
 *   4. Write user PATH entry via PowerShell
 *   5. Verify node / npm / claude are callable
 *
 * Usage: node.exe install-cli-tools.cjs
 *
 * Uses ONLY Node.js built-in modules — no npm dependencies.
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

// ---------------------------------------------------------------------------
// Paths
// ---------------------------------------------------------------------------

/** Resources directory inside the installer ($INSTDIR\resources) */
const resourcesDir = path.resolve(path.dirname(process.argv[1] || __dirname));

/** Bundled Node.js source: resources/bundled-node/win32-x64/ */
const bundledNodeSrc = path.join(resourcesDir, 'bundled-node', 'win32-x64');

/** Bundled Claude Code source: resources/claude-code/ */
const bundledClaudeSrc = path.join(resourcesDir, 'claude-code');

/** Installation target root */
const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
const cliRoot = path.join(localAppData, 'BondClaw', 'cli');
const binDir = path.join(cliRoot, 'bin');
const nodeRuntimeDir = path.join(cliRoot, 'runtime', 'node');
const claudeRuntimeDir = path.join(cliRoot, 'runtime', 'claude-code');

// ---------------------------------------------------------------------------
// Helpers
// ---------------------------------------------------------------------------

function log(msg) {
  console.log(`[BondClaw CLI] ${msg}`);
}

function warn(msg) {
  console.warn(`[BondClaw CLI] WARNING: ${msg}`);
}

function err(msg) {
  console.error(`[BondClaw CLI] ERROR: ${msg}`);
}

function asWinPath(p) {
  return p.replace(/\//g, '\\');
}

function exists(p) {
  return fs.existsSync(p);
}

function ensureDir(dir) {
  fs.mkdirSync(dir, { recursive: true });
}

function removeDir(dir) {
  if (fs.existsSync(dir)) {
    fs.rmSync(dir, { recursive: true, force: true });
  }
}

function copyDir(src, dest) {
  removeDir(dest);
  fs.cpSync(src, dest, { recursive: true, force: true, dereference: true });
}

function writeFile(filePath, content) {
  ensureDir(path.dirname(filePath));
  fs.writeFileSync(filePath, content, 'utf8');
}

function normalizePathEntry(value) {
  return value.trim().replace(/^"+|"+$/g, '').replace(/[\\/]+$/, '').toLowerCase();
}

function readUserPathFromRegistry() {
  const result = spawnSync('reg.exe', ['query', 'HKCU\\Environment', '/v', 'Path'], {
    encoding: 'utf8',
    windowsHide: true,
    timeout: 10_000,
  });

  if (result.error) {
    throw result.error;
  }

  const output = `${result.stdout || ''}\n${result.stderr || ''}`.trim();
  if (result.status !== 0) {
    if (/unable to find|找不到/i.test(output)) {
      return { type: 'REG_EXPAND_SZ', value: '' };
    }

    throw new Error(output || `reg query failed with status ${result.status}`);
  }

  const lines = output.split(/\r?\n/).reverse();
  for (const line of lines) {
    const match = line.match(/^\s*Path\s+(REG_\w+)\s+(.*)$/i);
    if (match) {
      return {
        type: match[1].toUpperCase(),
        value: (match[2] || '').trim(),
      };
    }
  }

  return { type: 'REG_EXPAND_SZ', value: '' };
}

function broadcastEnvironmentChange() {
  const psScript = [
    "$signature = '[DllImport(\"user32.dll\", SetLastError=true, CharSet=CharSet.Auto)] public static extern IntPtr SendMessageTimeout(IntPtr hWnd, int Msg, IntPtr wParam, string lParam, int fuFlags, int uTimeout, out IntPtr lpdwResult);'",
    "Add-Type -Namespace Win32 -Name NativeMethods -MemberDefinition $signature",
    "$result = [IntPtr]::Zero",
    "[void][Win32.NativeMethods]::SendMessageTimeout([IntPtr]0xffff, 0x001A, [IntPtr]::Zero, 'Environment', 0x0002, 5000, [ref]$result)",
  ].join('; ');

  const result = spawnSync('powershell.exe', ['-NoProfile', '-NonInteractive', '-Command', psScript], {
    encoding: 'utf8',
    windowsHide: true,
    timeout: 10_000,
  });

  if (result.error || result.status !== 0) {
    warn('PATH was written, but failed to broadcast environment change notification.');
    warn('  New terminals may require signing out or restarting Explorer to see the updated PATH immediately.');
    return false;
  }

  return true;
}

function prependCurrentProcessPath(binDirWin) {
  const current = process.env.PATH || '';
  const normalizedCurrent = current
    .split(';')
    .map(normalizePathEntry)
    .filter(Boolean);

  if (!normalizedCurrent.includes(normalizePathEntry(binDirWin))) {
    process.env.PATH = `${binDirWin};${current}`;
  }
}

// ---------------------------------------------------------------------------
// Phase 1: Check bundled resources exist
// ---------------------------------------------------------------------------

function checkBundledResources() {
  log('Checking bundled resources...');

  const checks = [
    ['bundled-node source', bundledNodeSrc],
    ['node.exe', path.join(bundledNodeSrc, 'node.exe')],
    ['npm-cli.js', path.join(bundledNodeSrc, 'node_modules', 'npm', 'bin', 'npm-cli.js')],
    ['npx-cli.js', path.join(bundledNodeSrc, 'node_modules', 'npm', 'bin', 'npx-cli.js')],
    ['claude-code source', bundledClaudeSrc],
    ['claude cli.js', path.join(bundledClaudeSrc, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')],
  ];

  let allOk = true;
  for (const [label, p] of checks) {
    if (!exists(p)) {
      err(`Missing: ${label} at ${p}`);
      allOk = false;
    } else {
      log(`  Found: ${label}`);
    }
  }
  return allOk;
}

// ---------------------------------------------------------------------------
// Phase 2: Check if already installed (skip reinstall)
// ---------------------------------------------------------------------------

function isAlreadyInstalled() {
  const nodeExe = path.join(nodeRuntimeDir, 'node.exe');
  const claudeCli = path.join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');
  const nodeCmd = path.join(binDir, 'node.cmd');
  const claudeCmd = path.join(binDir, 'claude.cmd');

  return exists(nodeExe) && exists(claudeCli) && exists(nodeCmd) && exists(claudeCmd);
}

// ---------------------------------------------------------------------------
// Phase 3: Deploy Node.js runtime
// ---------------------------------------------------------------------------

function deployNodeRuntime() {
  log('Deploying Node.js runtime...');
  log(`  Source: ${bundledNodeSrc}`);
  log(`  Target: ${nodeRuntimeDir}`);

  copyDir(bundledNodeSrc, nodeRuntimeDir);

  const nodeExe = path.join(nodeRuntimeDir, 'node.exe');
  if (!exists(nodeExe)) {
    throw new Error('node.exe not found after copy');
  }

  // Verify it runs
  const version = execSync(`"${asWinPath(nodeExe)}" --version`, {
    encoding: 'utf8',
    timeout: 10_000,
  }).trim();
  log(`  Node.js version: ${version}`);

  return true;
}

// ---------------------------------------------------------------------------
// Phase 4: Deploy Claude Code
// ---------------------------------------------------------------------------

function deployClaudeCode() {
  log('Deploying Claude Code...');
  log(`  Source: ${bundledClaudeSrc}`);
  log(`  Target: ${claudeRuntimeDir}`);

  copyDir(bundledClaudeSrc, claudeRuntimeDir);

  const claudeCli = path.join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js');
  if (!exists(claudeCli)) {
    throw new Error('Claude Code cli.js not found after copy');
  }

  log('  Claude Code deployed.');
  return true;
}

// ---------------------------------------------------------------------------
// Phase 5: Generate .cmd wrappers
// ---------------------------------------------------------------------------

function createWrappers() {
  log('Generating .cmd wrappers...');

  ensureDir(binDir);

  const nodeExe = asWinPath(path.join(nodeRuntimeDir, 'node.exe'));
  const npmCli = asWinPath(path.join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npm-cli.js'));
  const npxCli = asWinPath(path.join(nodeRuntimeDir, 'node_modules', 'npm', 'bin', 'npx-cli.js'));
  const claudeCli = asWinPath(
    path.join(claudeRuntimeDir, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')
  );

  const wrappers = {
    'node.cmd': `@echo off\r\n"${nodeExe}" %*\r\n`,
    'npm.cmd': `@echo off\r\n"${nodeExe}" "${npmCli}" %*\r\n`,
    'npx.cmd': `@echo off\r\n"${nodeExe}" "${npxCli}" %*\r\n`,
    'claude.cmd': `@echo off\r\n"${nodeExe}" "${claudeCli}" %*\r\n`,
  };

  for (const [name, content] of Object.entries(wrappers)) {
    writeFile(path.join(binDir, name), content);
    log(`  Created: ${name}`);
  }

  return true;
}

// ---------------------------------------------------------------------------
// Phase 6: Write user PATH
// ---------------------------------------------------------------------------

function writeUserPath() {
  log('Writing user PATH entry...');

  const binDirWin = asWinPath(binDir);
  const binDirNorm = normalizePathEntry(binDirWin);

  let currentUserPath = '';
  let currentUserPathType = 'REG_EXPAND_SZ';
  try {
    const pathInfo = readUserPathFromRegistry();
    currentUserPath = pathInfo.value;
    currentUserPathType = pathInfo.type === 'REG_SZ' ? 'REG_SZ' : 'REG_EXPAND_SZ';
  } catch (e) {
    warn('Failed to read user PATH from registry, skipping PATH write.');
    warn(`  Details: ${e.message}`);
    warn(`  You can manually add to PATH: ${binDirWin}`);
    return false;
  }

  // Check if already present (dedup)
  const parts = currentUserPath.split(';').map(normalizePathEntry).filter(Boolean);
  if (parts.includes(binDirNorm)) {
    log('  PATH entry already present, skipping.');
    prependCurrentProcessPath(binDirWin);
    return true;
  }

  // Prepend our bin directory
  const merged = [binDirWin, ...currentUserPath.split(';').map(p => p.trim()).filter(Boolean)].join(';');

  const result = spawnSync(
    'reg.exe',
    ['add', 'HKCU\\Environment', '/v', 'Path', '/t', currentUserPathType, '/d', merged, '/f'],
    {
      encoding: 'utf8',
      windowsHide: true,
      timeout: 10_000,
    }
  );

  if (result.error || (typeof result.status === 'number' && result.status !== 0)) {
    warn(`Failed to write user PATH (status: ${result.status}).`);
    const details = `${result.stdout || ''}\n${result.stderr || ''}`.trim();
    if (details) {
      warn(`  Details: ${details}`);
    }
    warn(`  CLI tools are deployed but not on PATH.`);
    warn(`  Please manually add to PATH: ${binDirWin}`);
    return false;
  }

  log(`  PATH entry written: ${binDirWin}`);
  prependCurrentProcessPath(binDirWin);
  broadcastEnvironmentChange();
  return true;
}

// ---------------------------------------------------------------------------
// Phase 7: Verify installation
// ---------------------------------------------------------------------------

function verify() {
  log('Verifying installation...');

  // Test wrappers directly
  const nodeCmd = asWinPath(path.join(binDir, 'node.cmd'));
  const npmCmd = asWinPath(path.join(binDir, 'npm.cmd'));
  const claudeCmd = asWinPath(path.join(binDir, 'claude.cmd'));

  // node --version
  try {
    const nodeVer = execSync(`"${nodeCmd}" --version`, {
      encoding: 'utf8', timeout: 10_000, windowsHide: true,
    }).trim();
    log(`  node --version: ${nodeVer}`);
  } catch (e) {
    throw new Error(`node.cmd verification failed: ${e.message}`);
  }

  // npm --version
  try {
    const npmVer = execSync(`"${npmCmd}" --version`, {
      encoding: 'utf8', timeout: 10_000, windowsHide: true,
    }).trim();
    log(`  npm --version: ${npmVer}`);
  } catch (e) {
    throw new Error(`npm.cmd verification failed: ${e.message}`);
  }

  // claude --version (may exit non-zero, that's OK as long as it runs)
  try {
    const claudeVer = execSync(`"${claudeCmd}" --version`, {
      encoding: 'utf8', timeout: 15_000, windowsHide: true,
    }).trim();
    log(`  claude --version: ${claudeVer}`);
  } catch (e) {
    // Non-zero exit is acceptable — some claude versions exit non-zero for --version
    const stdout = e.stdout ? e.stdout.toString().trim() : '';
    if (e.status !== null && e.status !== undefined) {
      log(`  claude --version: (exit ${e.status}${stdout ? `, output: ${stdout}` : ''})`);
    } else {
      throw new Error(`claude.cmd verification failed: ${e.message}`);
    }
  }

  return true;
}

// ---------------------------------------------------------------------------
// Main
// ---------------------------------------------------------------------------

function main() {
  log('========================================');
  log('BondClaw CLI Deployment');
  log('========================================');
  log(`Resources: ${resourcesDir}`);
  log(`Target:    ${cliRoot}`);
  log('');

  try {
    // Phase 1: Check bundled resources
    if (!checkBundledResources()) {
      err('Bundled resources incomplete. Cannot deploy CLI tools.');
      process.exit(1);
    }

    // Phase 2: Skip if already installed
    if (isAlreadyInstalled()) {
      log('CLI tools already installed, skipping deployment.');
      process.exit(0);
    }

    // Phase 3: Deploy Node.js
    deployNodeRuntime();

    // Phase 4: Deploy Claude Code
    deployClaudeCode();

    // Phase 5: Generate wrappers
    createWrappers();

    // Phase 6: Write PATH (best-effort, non-blocking)
    const pathOk = writeUserPath();

    // Phase 7: Verify
    verify();

    log('');
    log('========================================');
    log('CLI deployment complete.');
    if (!pathOk) {
      log('');
      log('NOTE: PATH was not updated automatically.');
      log(`Please add to your user PATH: ${asWinPath(binDir)}`);
      log('Then open a new terminal window.');
    }
    log('========================================');
    process.exit(0);
  } catch (e) {
    err(`Deployment failed: ${e.message}`);
    err('Stack: ' + (e.stack || 'N/A'));

    // Attempt cleanup on failure
    try {
      log('Attempting cleanup...');
      removeDir(cliRoot);
      log('Cleaned up partial installation.');
    } catch {
      warn('Cleanup also failed — manual cleanup may be needed.');
    }

    process.exit(1);
  }
}

main();
