#!/usr/bin/env node

import path from 'node:path';
import { spawnSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const justToolsPath = path.join(scriptDir, 'just-tools.mjs');

const passthroughCommands = new Set([
  'preflight',
  'info',
  'rebuild-native',
  'verify-native',
  'build-win-x64',
  'build-win-arm64',
  'build-win',
  'build-mac-arm64',
  'build-mac-x64',
  'build-mac',
  'build-linux',
  'clean',
  'clean-all',
  'list-artifacts',
]);

const args = process.argv.slice(2);
const normalizedArgs = args.map((arg) => String(arg).toLowerCase());

const deriveCommand = () => {
  if (args.length === 0) {
    return 'build-win';
  }

  const first = String(args[0]).toLowerCase();
  if (passthroughCommands.has(first)) {
    return first;
  }

  if (normalizedArgs.includes('--win')) {
    if (normalizedArgs.includes('--arm64') && !normalizedArgs.includes('--x64')) {
      return 'build-win-arm64';
    }
    if (normalizedArgs.includes('--x64') && !normalizedArgs.includes('--arm64')) {
      return 'build-win-x64';
    }
    return 'build-win';
  }

  if (normalizedArgs.includes('--mac')) {
    if (normalizedArgs.includes('--arm64') && !normalizedArgs.includes('--x64')) {
      return 'build-mac-arm64';
    }
    if (normalizedArgs.includes('--x64') && !normalizedArgs.includes('--arm64')) {
      return 'build-mac-x64';
    }
    return 'build-mac';
  }

  if (normalizedArgs.includes('--linux')) {
    return 'build-linux';
  }

  return 'build-win';
};

const command = deriveCommand();
const result = spawnSync(process.execPath, [justToolsPath, command], {
  cwd: path.resolve(scriptDir, '..'),
  env: process.env,
  stdio: 'inherit',
  shell: false,
});

if (result.error) {
  console.error(result.error);
  process.exit(1);
}

process.exit(typeof result.status === 'number' ? result.status : 0);
