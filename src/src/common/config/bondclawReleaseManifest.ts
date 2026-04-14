/**
 * @license
 * Copyright 2025 BondClaw
 * SPDX-License-Identifier: Apache-2.0
 */

import releaseManifest from './bondclaw-release-manifest.example.json';
import baseBrand from './bondclaw-brand.json';

export type BondClawBrandConfig = {
  appName: string;
  productName: string;
  teamLabel: string;
  splashCopy: string;
  supportRibbonCopy: string;
  supportBannerCopy: string;
  attributionPolicy: string;
  officialWebsite: string;
  docsBaseUrl: string;
  githubRepository: string;
  releaseNotesUrl: string;
  supportUrl: string;
  updateHosts: string[];
  researchFeedUrl?: string;
  registrationApiBaseUrl?: string;
};

export type BondClawReleaseDistribution = {
  updateRepo: string;
  updateHosts: string[];
  manifestUrl?: string;
};

export type BondClawReleaseManifest = {
  schemaVersion: number;
  releaseChannel: string;
  releaseVersion: string;
  branding?: Partial<Omit<BondClawBrandConfig, 'updateHosts'>>;
  distribution?: Partial<BondClawReleaseDistribution>;
  featureFlags?: Record<string, boolean>;
};

const baseBrandConfig = baseBrand as BondClawBrandConfig;
const manifestConfig = releaseManifest as BondClawReleaseManifest;

const mergeBrandConfig = (): BondClawBrandConfig => {
  const branding = manifestConfig.branding ?? {};
  const distribution = manifestConfig.distribution ?? {};
  const updateHosts = distribution.updateHosts ?? baseBrandConfig.updateHosts;

  return {
    ...baseBrandConfig,
    ...branding,
    updateHosts: [...updateHosts],
  };
};

export const getBondClawReleaseManifest = (): BondClawReleaseManifest => manifestConfig;

export const getBondClawReleaseHostConfig = (): BondClawReleaseDistribution => ({
  updateRepo: manifestConfig.distribution?.updateRepo || baseBrandConfig.githubRepository,
  updateHosts: [...(manifestConfig.distribution?.updateHosts ?? baseBrandConfig.updateHosts)],
  manifestUrl: manifestConfig.distribution?.manifestUrl,
});

export const getBondClawBrandConfig = (): BondClawBrandConfig => mergeBrandConfig();

export const getBondClawAppName = (): string => getBondClawBrandConfig().appName;

export const getBondClawTeamLabel = (): string => getBondClawBrandConfig().teamLabel;

export const getBondClawRepository = (): string => getBondClawReleaseHostConfig().updateRepo;

export const getBondClawWebsite = (): string => getBondClawBrandConfig().officialWebsite;

export const getBondClawSupportUrl = (): string => getBondClawBrandConfig().supportUrl;

export const getBondClawDocsBaseUrl = (): string => getBondClawBrandConfig().docsBaseUrl;

export const getBondClawReleaseNotesUrl = (): string => getBondClawBrandConfig().releaseNotesUrl;

export const getBondClawUpdateHosts = (): string[] => [...getBondClawReleaseHostConfig().updateHosts];

export const getBondClawUserAgent = (): string => getBondClawBrandConfig().appName;

export const getBondClawResearchFeedUrl = (): string | undefined => getBondClawBrandConfig().researchFeedUrl;

export const getBondClawRegistrationApiBaseUrl = (): string =>
  getBondClawBrandConfig().registrationApiBaseUrl?.trim() || 'https://bondclawverify-fimemwznlg.cn-hangzhou.fcapp.run';

export const getBondClawRuntimeManifestUrl = (): string | undefined =>
  manifestConfig.distribution?.manifestUrl?.trim() || process.env.BONDCLAW_RELEASE_MANIFEST_URL?.trim() || undefined;
