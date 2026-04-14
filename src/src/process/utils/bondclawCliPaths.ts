/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import os from 'node:os';
import path from 'node:path';

/**
 * Current-user installation root for BondClaw-managed CLI tools.
 *
 * We keep the install outside the app bundle so the resulting `node`, `npm`,
 * and `claude` commands behave like a real user-level installation and remain
 * available after the app exits.
 */
export function getBondClawCliRoot(): string {
  if (process.platform === 'win32') {
    const localAppData = process.env.LOCALAPPDATA || path.join(os.homedir(), 'AppData', 'Local');
    return path.join(localAppData, 'BondClaw', 'cli');
  }

  return path.join(os.homedir(), '.bondclaw', 'cli');
}

/**
 * User-level bin directory that should be added to PATH.
 */
export function getBondClawCliBinDir(): string {
  return path.join(getBondClawCliRoot(), 'bin');
}

/**
 * Directory containing the staged Node/npm runtime.
 */
export function getBondClawNodeRuntimeDir(): string {
  return path.join(getBondClawCliRoot(), 'runtime', 'node');
}

/**
 * Directory containing the staged Claude Code package.
 */
export function getBondClawClaudeRuntimeDir(): string {
  return path.join(getBondClawCliRoot(), 'runtime', 'claude-code');
}

/**
 * Absolute path to the staged node executable, if installed.
 */
export function getBondClawNodeExe(): string {
  return path.join(getBondClawCliBinDir(), process.platform === 'win32' ? 'node.exe' : 'node');
}

/**
 * Absolute path to the staged Claude Code command wrapper, if installed.
 */
export function getBondClawClaudeCmd(): string {
  return path.join(getBondClawCliBinDir(), process.platform === 'win32' ? 'claude.cmd' : 'claude');
}

