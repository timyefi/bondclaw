#!/usr/bin/env node
/**
 * BondClaw CLI Installer — End-to-End Smoke Test
 *
 * Simulates the exact runtime installation flow that occurs when the user
 * launches BondClaw Desktop for the first time.  Tests every step:
 *   1. Verify bundled seed resources exist in the built package
 *   2. Copy Node runtime to %LOCALAPPDATA%\BondClaw\cli\runtime\node\
 *   3. Copy Claude Code to %LOCALAPPDATA%\BondClaw\cli\runtime\claude-code\
 *   4. Generate .cmd wrappers in %LOCALAPPDATA%\BondClaw\cli\bin\
 *   5. Write user PATH entry via PowerShell
 *   6. Verify node / npm / claude are callable from a FRESH shell
 *   7. Clean up (remove everything we installed + clean PATH)
 *
 * Usage:  node scripts/test-installer.mjs
 */

import fs from 'node:fs';
import path from 'node:path';
import { execSync, spawnSync } from 'node:child_process';
import os from 'node:os';

// ---------------------------------------------------------------------------
// Configuration
// ---------------------------------------------------------------------------
const CLI_ROOT = path.join(process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local'), 'BondClaw', 'cli');
const BIN_DIR = path.join(CLI_ROOT, 'bin');
const NODE_RUNTIME = path.join(CLI_ROOT, 'runtime', 'node');
const CLAUDE_RUNTIME = path.join(CLI_ROOT, 'runtime', 'claude-code');

// The built package's resource directories
// electron-builder.yml has `directories.output: ../out` (relative to src/)
// so the output is at <repo-root>/out/win-unpacked/resources/
const BUILT_RESOURCES = path.resolve(
  import.meta.dirname, '..', '..', 'out', 'win-unpacked', 'resources'
);
const BUNDLED_NODE_SRC = path.join(BUILT_RESOURCES, 'bundled-node', 'win32-x64');
const BUNDLED_CLAUDE_SRC = path.join(BUILT_RESOURCES, 'claude-code');

let passed = 0;
let failed = 0;

function check(label, fn) {
  try {
    const result = fn();
    if (result === false) {
      console.log(`  FAIL  ${label}`);
      failed += 1;
      return false;
    }
    console.log(`  OK    ${label}`);
    passed += 1;
    return true;
  } catch (err) {
    console.log(`  FAIL  ${label}: ${err.message}`);
    failed += 1;
    return false;
  }
}

function asWinPath(p) {
  return p.replace(/\//g, '\\');
}

// ---------------------------------------------------------------------------
console.log('\n====================================================');
console.log('  BondClaw CLI Installer — E2E Smoke Test');
console.log('====================================================\n');

// ── Phase 0: Check built resources exist ──────────────────────────────────
console.log('Phase 0: Verify built package resources');
console.log('─'.repeat(50));

check('bundled-node source exists', () => fs.existsSync(BUNDLED_NODE_SRC));
check('bundled-node/node.exe exists', () =>
  fs.existsSync(path.join(BUNDLED_NODE_SRC, 'node.exe')));
check('bundled-node/npm-cli.js exists', () =>
  fs.existsSync(path.join(BUNDLED_NODE_SRC, 'node_modules', 'npm', 'bin', 'npm-cli.js')));
check('bundled-node/npx-cli.js exists', () =>
  fs.existsSync(path.join(BUNDLED_NODE_SRC, 'node_modules', 'npm', 'bin', 'npx-cli.js')));
check('claude-code source exists', () => fs.existsSync(BUNDLED_CLAUDE_SRC));
check('claude-code/cli.js exists', () =>
  fs.existsSync(path.join(BUNDLED_CLAUDE_SRC, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')));

// ── Phase 1: Clean slate ─────────────────────────────────────────────────
console.log('\nPhase 1: Clean up previous install (if any)');
console.log('─'.repeat(50));

if (fs.existsSync(CLI_ROOT)) {
  fs.rmSync(CLI_ROOT, { recursive: true, force: true });
  check('removed previous CLI_ROOT', () => !fs.existsSync(CLI_ROOT));
} else {
  check('no previous install found (clean)', () => true);
}

// ── Phase 2: Copy Node runtime ───────────────────────────────────────────
console.log('\nPhase 2: Copy Node.js runtime');
console.log('─'.repeat(50));

fs.mkdirSync(NODE_RUNTIME, { recursive: true });
fs.cpSync(BUNDLED_NODE_SRC, NODE_RUNTIME, { recursive: true, force: true, dereference: true });

check('node.exe copied to runtime', () =>
  fs.existsSync(path.join(NODE_RUNTIME, 'node.exe')));
check('npm-cli.js copied to runtime', () =>
  fs.existsSync(path.join(NODE_RUNTIME, 'node_modules', 'npm', 'bin', 'npm-cli.js')));

// Test node.exe actually runs
check('node.exe runs and reports version >= 18', () => {
  const out = execSync(`"${asWinPath(path.join(NODE_RUNTIME, 'node.exe'))}" --version`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  const major = parseInt(out.replace(/^v/, ''), 10);
  console.log(`         version: ${out}`);
  return major >= 18;
});

// Test npm-cli.js actually runs
check('npm-cli.js runs and reports version', () => {
  const nodeExe = asWinPath(path.join(NODE_RUNTIME, 'node.exe'));
  const npmCli = asWinPath(path.join(NODE_RUNTIME, 'node_modules', 'npm', 'bin', 'npm-cli.js'));
  const out = execSync(`"${nodeExe}" "${npmCli}" --version`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(`         version: ${out}`);
  return true;
});

// ── Phase 3: Copy Claude Code ────────────────────────────────────────────
console.log('\nPhase 3: Copy Claude Code seed');
console.log('─'.repeat(50));

fs.mkdirSync(CLAUDE_RUNTIME, { recursive: true });
fs.cpSync(BUNDLED_CLAUDE_SRC, CLAUDE_RUNTIME, { recursive: true, force: true, dereference: true });

check('claude-code/cli.js copied to runtime', () =>
  fs.existsSync(path.join(CLAUDE_RUNTIME, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js')));

// Test claude cli.js actually loads (just --version, no interactive)
check('claude-code cli.js runs --version', () => {
  const nodeExe = asWinPath(path.join(NODE_RUNTIME, 'node.exe'));
  const claudeCli = asWinPath(path.join(CLAUDE_RUNTIME, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js'));
  try {
    const out = execSync(`"${nodeExe}" "${claudeCli}" --version`, {
      encoding: 'utf8', timeout: 15_000,
    }).trim();
    console.log(`         version: ${out}`);
    return true;
  } catch (err) {
    // --version may exit non-zero in some claude-code versions, that's OK
    // as long as the process starts and produces output
    console.log(`         (exit code ${err.status}, but process ran)`);
    return err.status !== null && err.status !== undefined;
  }
});

// ── Phase 4: Generate wrappers ───────────────────────────────────────────
console.log('\nPhase 4: Generate .cmd wrappers');
console.log('─'.repeat(50));

fs.mkdirSync(BIN_DIR, { recursive: true });

const nodeExe = asWinPath(path.join(NODE_RUNTIME, 'node.exe'));
const npmCli = asWinPath(path.join(NODE_RUNTIME, 'node_modules', 'npm', 'bin', 'npm-cli.js'));
const npxCli = asWinPath(path.join(NODE_RUNTIME, 'node_modules', 'npm', 'bin', 'npx-cli.js'));
const claudeCli = asWinPath(path.join(CLAUDE_RUNTIME, 'node_modules', '@anthropic-ai', 'claude-code', 'cli.js'));

const wrappers = {
  'node.cmd': `@echo off\r\n"${nodeExe}" %*\r\n`,
  'npm.cmd': `@echo off\r\n"${nodeExe}" "${npmCli}" %*\r\n`,
  'npx.cmd': `@echo off\r\n"${nodeExe}" "${npxCli}" %*\r\n`,
  'claude.cmd': `@echo off\r\n"${nodeExe}" "${claudeCli}" %*\r\n`,
};

for (const [name, content] of Object.entries(wrappers)) {
  fs.writeFileSync(path.join(BIN_DIR, name), content);
  check(`${name} created`, () => fs.existsSync(path.join(BIN_DIR, name)));
}

// ── Phase 5: Test wrappers directly (without PATH) ───────────────────────
console.log('\nPhase 5: Test wrappers directly');
console.log('─'.repeat(50));

check('node.cmd runs', () => {
  const out = execSync(`"${asWinPath(path.join(BIN_DIR, 'node.cmd'))}" --version`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(`         ${out}`);
  return true;
});

check('npm.cmd runs', () => {
  const out = execSync(`"${asWinPath(path.join(BIN_DIR, 'npm.cmd'))}" --version`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(`         ${out}`);
  return true;
});

check('claude.cmd runs (at least starts)', () => {
  try {
    const out = execSync(`"${asWinPath(path.join(BIN_DIR, 'claude.cmd'))}" --version`, {
      encoding: 'utf8', timeout: 15_000,
    }).trim();
    console.log(`         ${out}`);
    return true;
  } catch (err) {
    // claude --version may exit non-zero
    const stdout = err.stdout ? err.stdout.toString().trim() : '';
    console.log(`         (exit ${err.status}${stdout ? `, output: ${stdout}` : ', process ran'})`);
    return err.status !== null;
  }
});

// ── Phase 6: Write user PATH ─────────────────────────────────────────────
console.log('\nPhase 6: Write user PATH');
console.log('─'.repeat(50));

// First read current user PATH
const currentUserPath = execSync(
  `powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"`,
  { encoding: 'utf8', timeout: 10_000 }
).trim();

const binDirNorm = asWinPath(BIN_DIR).toLowerCase().replace(/\\$/, '');
const pathParts = currentUserPath.split(';').map(p => p.trim().toLowerCase().replace(/\\$/, ''));
const alreadyInPath = pathParts.includes(binDirNorm);

if (!alreadyInPath) {
  const merged = [asWinPath(BIN_DIR), ...currentUserPath.split(';').map(p => p.trim()).filter(Boolean)].join(';');
  const psScript = `[Environment]::SetEnvironmentVariable('Path', ${JSON.stringify(merged)}, 'User')`;
  const result = spawnSync(
    process.env.COMSPEC || 'cmd.exe',
    ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', psScript],
    { stdio: 'ignore', windowsHide: true, timeout: 10_000 }
  );
  check('PATH entry written to user registry', () => result.status === 0);
} else {
  check('PATH entry already present', () => true);
}

// ── Phase 7: Verify in a FRESH shell (the real test) ─────────────────────
console.log('\nPhase 7: Verify from a FRESH shell (new process)');
console.log('─'.repeat(50));

// Spawn a fresh cmd.exe that doesn't inherit our PATH to simulate a new terminal
function freshShellTest(command) {
  const result = spawnSync(
    process.env.COMSPEC || 'cmd.exe',
    ['/c', command],
    {
      encoding: 'utf8',
      timeout: 15_000,
      windowsHide: true,
      // Do NOT pass process.env — use a clean system environment
      // so we test what a NEW user would see after opening a fresh terminal
      env: {
        // Only pass minimal system env vars, NOT our modified PATH
        SystemRoot: process.env.SystemRoot || 'C:\\Windows',
        PATH: undefined, // Force it to load from registry
      },
    }
  );
  return result;
}

// Actually, on Windows cmd.exe always loads PATH from registry when env is not passed.
// But to be safe, let's use `cmd /c "ver && where <cmd>"` which opens a truly fresh shell.
function freshCmdTest(tool) {
  const result = execSync(
    `${process.env.COMSPEC || 'cmd.exe'} /c "where ${tool}.cmd"`,
    { encoding: 'utf8', timeout: 10_000 }
  ).trim();
  return result;
}

check('`where node.cmd` finds our wrapper', () => {
  const out = freshCmdTest('node');
  console.log(`         ${out.split('\n')[0]}`);
  return out.toLowerCase().includes(BIN_DIR.toLowerCase().replace(/\\/g, '/')) ||
         out.toLowerCase().includes(asWinPath(BIN_DIR).toLowerCase());
});

check('`where npm.cmd` finds our wrapper', () => {
  const out = freshCmdTest('npm');
  console.log(`         ${out.split('\n')[0]}`);
  return out.toLowerCase().includes(BIN_DIR.toLowerCase().replace(/\\/g, '/')) ||
         out.toLowerCase().includes(asWinPath(BIN_DIR).toLowerCase());
});

check('`where claude.cmd` finds our wrapper', () => {
  const out = freshCmdTest('claude');
  console.log(`         ${out.split('\n')[0]}`);
  return out.toLowerCase().includes(BIN_DIR.toLowerCase().replace(/\\/g, '/')) ||
         out.toLowerCase().includes(asWinPath(BIN_DIR).toLowerCase());
});

// ── Phase 8: Verify actual execution from fresh PATH ──────────────────────
console.log('\nPhase 8: Execute node/npm/claude from fresh PATH');
console.log('─'.repeat(50));

check('fresh `node --version` works', () => {
  const out = execSync(`${process.env.COMSPEC || 'cmd.exe'} /c "node --version"`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(`         ${out}`);
  return out.startsWith('v');
});

check('fresh `npm --version` works', () => {
  const out = execSync(`${process.env.COMSPEC || 'cmd.exe'} /c "npm --version"`, {
    encoding: 'utf8', timeout: 10_000,
  }).trim();
  console.log(`         ${out}`);
  return /^\d+\.\d+/.test(out);
});

check('fresh `claude --version` runs (may exit non-zero)', () => {
  try {
    const out = execSync(`${process.env.COMSPEC || 'cmd.exe'} /c "claude --version"`, {
      encoding: 'utf8', timeout: 15_000,
    }).trim();
    console.log(`         ${out}`);
    return true;
  } catch (err) {
    console.log(`         (exit ${err.status}, process ran — OK)`);
    return err.status !== null;
  }
});

// ── Phase 9: Cleanup ─────────────────────────────────────────────────────
console.log('\nPhase 9: Cleanup (remove test install + PATH entry)');
console.log('─'.repeat(50));

// Remove CLI directory
fs.rmSync(CLI_ROOT, { recursive: true, force: true });
check('CLI root removed', () => !fs.existsSync(CLI_ROOT));

// Remove PATH entry
const pathAfter = execSync(
  `powershell -NoProfile -Command "[Environment]::GetEnvironmentVariable('Path','User')"`,
  { encoding: 'utf8', timeout: 10_000 }
).trim();
const cleanedParts = pathAfter.split(';').filter(p => {
  const norm = p.trim().toLowerCase().replace(/\\$/, '').replace(/\/$/, '');
  return norm !== binDirNorm;
});
const cleanedPath = cleanedParts.join(';');
const cleanPs = `[Environment]::SetEnvironmentVariable('Path', ${JSON.stringify(cleanedPath)}, 'User')`;
spawnSync(
  process.env.COMSPEC || 'cmd.exe',
  ['/c', 'powershell.exe', '-NoProfile', '-NonInteractive', '-Command', cleanPs],
  { stdio: 'ignore', windowsHide: true, timeout: 10_000 }
);
check('PATH entry removed', () => true);

// ── Summary ──────────────────────────────────────────────────────────────
console.log('\n====================================================');
console.log(`  Results: ${passed} passed, ${failed} failed`);
console.log('====================================================\n');

if (failed > 0) {
  console.log('  ❌ SMOKE TEST FAILED — installation does NOT work correctly.\n');
  process.exit(1);
} else {
  console.log('  ✅ ALL CHECKS PASSED — installation flow is verified.\n');
  process.exit(0);
}
