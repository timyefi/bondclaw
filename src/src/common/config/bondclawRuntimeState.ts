/**
 * @license
 * Copyright 2025 BondClaw
 * SPDX-License-Identifier: Apache-2.0
 */

import {
  getBondClawBrandConfig,
  getBondClawReleaseManifest,
  type BondClawBrandConfig,
  type BondClawReleaseManifest,
} from './bondclawReleaseManifest';

export type BondClawRuntimeSource = 'bundled' | 'cache' | 'remote';

export type BondClawRuntimeSnapshot = {
  source: BondClawRuntimeSource;
  loadedAt: string;
  manifest: BondClawReleaseManifest;
  brand: BondClawBrandConfig;
};

const buildDefaultSnapshot = (): BondClawRuntimeSnapshot => ({
  source: 'bundled',
  loadedAt: new Date(0).toISOString(),
  manifest: getBondClawReleaseManifest(),
  brand: getBondClawBrandConfig(),
});

let currentRuntimeSnapshot = buildDefaultSnapshot();

export const buildBondClawRuntimeSnapshot = (
  manifest: BondClawReleaseManifest,
  source: BondClawRuntimeSource,
  loadedAt = new Date().toISOString()
): BondClawRuntimeSnapshot => {
  const baseBrand = getBondClawBrandConfig();
  const branding = manifest.branding ?? {};
  const distribution = manifest.distribution ?? {};

  return {
    source,
    loadedAt,
    manifest,
    brand: {
      ...baseBrand,
      ...branding,
      docsBaseUrl: branding.docsBaseUrl || baseBrand.docsBaseUrl,
      githubRepository: distribution.updateRepo || branding.githubRepository || baseBrand.githubRepository,
      updateHosts: [...(distribution.updateHosts ?? baseBrand.updateHosts)],
    },
  };
};

export const getBondClawRuntimeSnapshot = (): BondClawRuntimeSnapshot => currentRuntimeSnapshot;

export const setBondClawRuntimeSnapshot = (snapshot: BondClawRuntimeSnapshot): BondClawRuntimeSnapshot => {
  currentRuntimeSnapshot = snapshot;
  return currentRuntimeSnapshot;
};

export const resetBondClawRuntimeSnapshot = (): BondClawRuntimeSnapshot => {
  currentRuntimeSnapshot = buildDefaultSnapshot();
  return currentRuntimeSnapshot;
};

export const getBondClawRuntimeBrandConfig = (): BondClawBrandConfig => getBondClawRuntimeSnapshot().brand;
export const getBondClawRuntimeAppName = (): string => getBondClawRuntimeBrandConfig().appName;
export const getBondClawRuntimeTeamLabel = (): string => getBondClawRuntimeBrandConfig().teamLabel;
export const getBondClawRuntimeWebsite = (): string => getBondClawRuntimeBrandConfig().officialWebsite;
export const getBondClawRuntimeDocsBaseUrl = (): string => getBondClawRuntimeBrandConfig().docsBaseUrl;
export const getBondClawRuntimeSupportUrl = (): string => getBondClawRuntimeBrandConfig().supportUrl;
export const getBondClawRuntimeReleaseNotesUrl = (): string => getBondClawRuntimeBrandConfig().releaseNotesUrl;
export const getBondClawRuntimeRepository = (): string =>
  getBondClawRuntimeSnapshot().manifest.distribution?.updateRepo || getBondClawRuntimeBrandConfig().githubRepository;
export const getBondClawRuntimeUserAgent = (): string => getBondClawRuntimeBrandConfig().appName;
export const getBondClawRuntimeUpdateHosts = (): string[] => [...getBondClawRuntimeBrandConfig().updateHosts];
export const getBondClawRuntimeManifestUrl = (): string | undefined =>
  getBondClawRuntimeSnapshot().manifest.distribution?.manifestUrl?.trim() ||
  process.env.BONDCLAW_RELEASE_MANIFEST_URL?.trim() ||
  undefined;
