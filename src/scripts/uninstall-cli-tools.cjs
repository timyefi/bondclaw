#!/usr/bin/env node
// @ts-check
/**
 * BondClaw CLI Cleanup Script
 *
 * Run by the NSIS uninstaller to remove CLI tools and PATH entry.
 * Always exits 0 — cleanup failures do not block uninstall.
 *
 * Usage: node.exe uninstall-cli-tools.cjs
 */

const fs = require('fs');
const path = require('path');
const os = require('os');
const { execSync, spawnSync } = require('child_process');

function log(msg) {
  console.log(`[BondClaw Uninstall] ${msg}`);
}

function warn(msg) {
  console.warn(`[BondClaw Uninstall] WARNING: ${msg}`);
}

function asWinPath(p) {
  return p.replace(/\//g, '\\');
}

const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
const cliRoot = path.join(localAppData, 'BondClaw', 'cli');
const binDir = path.join(cliRoot, 'bin');

// ---------------------------------------------------------------------------
// 1. Remove CLI directory
// ---------------------------------------------------------------------------

try {
  if (fs.existsSync(cliRoot)) {
    fs.rmSync(cliRoot, { recursive: true, force: true });
    log(`Removed: ${asWinPath(cliRoot)}`);
  } else {
    log('CLI directory not found, nothing to remove.');
  }
} catch (e) {
  warn(`Failed to remove CLI directory: ${e.message}`);
}

// ---------------------------------------------------------------------------
// 2. Remove PATH entry from user registry
// ---------------------------------------------------------------------------

try {
  const binDirWin = asWinPath(binDir);
  const binDirNorm = binDirWin.toLowerCase().replace(/\\$/, '');

  // Read current user PATH
  const currentUserPath = execSync(
    'powershell.exe -NoProfile -NonInteractive -Command "[Environment]::GetEnvironmentVariable(\'Path\',\'User\')"',
    { encoding: 'utf8', timeout: 10_000, windowsHide: true }
  ).trim();

  // Remove our entry
  const parts = currentUserPath.split(';').filter(p => {
    const norm = p.trim().toLowerCase().replace(/\\$/, '').replace(/\/$/, '');
    return norm !== binDirNorm;
  });
  const cleanedPath = parts.join(';');

  // Write back
  const psScript = `[Environment]::SetEnvironmentVariable('Path', ${JSON.stringify(cleanedPath)}, 'User')`;
  spawnSync(
    process.env.COMSPEC || 'cmd.exe',
    ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', psScript],
    { stdio: 'ignore', windowsHide: true, timeout: 10_000 }
  );
  log('PATH entry removed.');
} catch (e) {
  warn(`Failed to clean PATH entry: ${e.message}`);
}

log('Cleanup complete.');
process.exit(0);
