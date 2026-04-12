/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { getPlatformServices } from '@/common/platform';

/**
 * Returns baseName unchanged in release builds, or baseName + '-dev' in dev builds.
 * When BONDCLAW_MULTI_INSTANCE=1 (or legacy AIONUI_MULTI_INSTANCE=1), appends '-2' to isolate the second dev instance.
 * Used to isolate symlink and directory names between environments.
 *
 * @example
 * getEnvAwareName('.bondclaw')        // release → '.bondclaw',        dev → '.bondclaw-dev'
 * getEnvAwareName('.bondclaw-config') // release → '.bondclaw-config', dev → '.bondclaw-config-dev'
 * // with BONDCLAW_MULTI_INSTANCE=1:  dev → '.bondclaw-dev-2'
 */
export function getEnvAwareName(baseName: string): string {
  if (getPlatformServices().paths.isPackaged() === true) return baseName;
  const suffix =
    process.env.BONDCLAW_MULTI_INSTANCE === '1' || process.env.AIONUI_MULTI_INSTANCE === '1' ? '-dev-2' : '-dev';
  return `${baseName}${suffix}`;
}
