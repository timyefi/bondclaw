/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { existsSync } from 'node:fs';
import { join } from 'node:path';

/**
 * Get the resources path (works in both packaged and development mode).
 * Follows the same pattern as getBundledBunDir() in shellEnv.ts.
 */
function getResourcesPath(): string {
  // In packaged mode, use process.resourcesPath from Electron
  const resourcesPath = (process as NodeJS.Process & { resourcesPath?: string }).resourcesPath;
  if (resourcesPath) {
    return resourcesPath;
  }
  // In development mode, use the resources directory relative to project root
  return join(process.cwd(), 'resources');
}

/**
 * Get the directory containing the bundled Node.js runtime.
 * Layout: resources/bundled-node/{platform}-{arch}/
 */
export function getBundledNodeDir(): string | null {
  const resourcesPath = getResourcesPath();
  const platform = process.platform;
  const arch = process.arch;
  const dir = join(resourcesPath, 'bundled-node', `${platform}-${arch}`);
  const exeName = platform === 'win32' ? 'node.exe' : 'bin/node';
  return existsSync(join(dir, exeName)) ? dir : null;
}

/**
 * Get the absolute path to the bundled node executable.
 */
export function getBundledNodeExe(): string | null {
  const dir = getBundledNodeDir();
  if (!dir) return null;
  const exe = join(dir, process.platform === 'win32' ? 'node.exe' : 'bin/node');
  return existsSync(exe) ? exe : null;
}

/**
 * Get the bundled npm CLI entry point.
 * This is expected to exist when the packaged Node runtime is seeded fully.
 */
export function getBundledNpmCli(): string | null {
  const dir = getBundledNodeDir();
  if (!dir) return null;
  const npmCli = join(dir, 'node_modules', 'npm', 'bin', 'npm-cli.js');
  return existsSync(npmCli) ? npmCli : null;
}

/**
 * Get the bundled npx CLI entry point.
 */
export function getBundledNpxCli(): string | null {
  const dir = getBundledNodeDir();
  if (!dir) return null;
  const npxCli = join(dir, 'node_modules', 'npm', 'bin', 'npx-cli.js');
  return existsSync(npxCli) ? npxCli : null;
}

/**
 * Get the root directory of the bundled Claude Code seed package.
 * Layout: resources/claude-code/
 */
export function getBundledClaudePackageRoot(): string | null {
  const resourcesPath = getResourcesPath();
  const root = join(resourcesPath, 'claude-code');
  const packageJson = join(root, 'package.json');
  return existsSync(packageJson) ? root : null;
}

/**
 * Get the directory containing the bundled Claude Code bin wrappers.
 * Layout: resources/claude-code/node_modules/.bin/
 */
export function getBundledClaudeDir(): string | null {
  const root = getBundledClaudePackageRoot();
  if (!root) return null;
  const binDir = join(root, 'node_modules', '.bin');
  return existsSync(binDir) ? binDir : null;
}
