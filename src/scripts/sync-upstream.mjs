#!/usr/bin/env node

import { execSync } from 'node:child_process';
import { fileURLToPath } from 'node:url';
import path from 'node:path';

const scriptDir = path.dirname(fileURLToPath(import.meta.url));
const rootDir = path.resolve(scriptDir, '..');

const run = (command) =>
  execSync(command, {
    cwd: rootDir,
    stdio: 'pipe',
    encoding: 'utf8',
  }).trim();

const fail = (message) => {
  console.error(message);
  process.exit(1);
};

const assertCleanWorktree = () => {
  const status = run('git status --porcelain');
  if (status) {
    fail(['Worktree is not clean.', 'Commit or stash local changes before syncing upstream.', '', status].join('\n'));
  }
};

const resolveUpstreamRef = () => {
  try {
    const remoteInfo = run('git remote show upstream');
    const match = remoteInfo.match(/HEAD branch:\s*(\S+)/);
    const branch = match?.[1] || 'main';
    return `upstream/${branch}`;
  } catch {
    return 'upstream/main';
  }
};

try {
  assertCleanWorktree();

  const upstreamRef = resolveUpstreamRef();
  console.log(`Fetching upstream and merging ${upstreamRef}...`);
  run('git fetch upstream --prune');
  run(`git merge --no-edit ${upstreamRef}`);
  console.log('Upstream sync complete.');
} catch (error) {
  fail(error instanceof Error ? error.message : String(error));
}
