/**
 * @license
 * Copyright 2025 BondClaw (https://github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

export type BondClawRegistration = {
  name: string;
  institution: string;
  phone: string;
  email: string;
  registeredAt: string;
};

const STORAGE_KEY = 'bondclaw.registration';
const SYNC_ENDPOINT = 'https://github.com/timyefi/bondclaw/api/register';

export function getBondClawRegistration(): BondClawRegistration | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    return JSON.parse(raw) as BondClawRegistration;
  } catch {
    return null;
  }
}

export function setBondClawRegistration(data: BondClawRegistration): void {
  localStorage.setItem(STORAGE_KEY, JSON.stringify(data));
  syncBondClawRegistration(data).catch(() => {});
}

export function isBondClawRegistered(): boolean {
  const reg = getBondClawRegistration();
  return Boolean(reg?.name && reg?.institution && reg?.phone && reg?.email);
}

/** Non-blocking sync to backend — errors are silently ignored */
export async function syncBondClawRegistration(data: BondClawRegistration): Promise<void> {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 5000);
    await fetch(SYNC_ENDPOINT, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(data),
      signal: controller.signal,
    });
    clearTimeout(timeoutId);
  } catch {
    // Silently fail — registration is stored locally regardless
  }
}
