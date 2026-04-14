/**
 * @license
 * Copyright 2025 BondClaw (https://github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { getBondClawRegistrationApiBaseUrl } from './bondclawBrand';

export type BondClawRegistration = {
  name: string;
  institution: string;
  phone: string;
  email: string;
  registeredAt: string;
  verified: boolean;
  verifiedAt?: string;
  version?: string;
  source?: string;
};

export type SendVerificationCodeResponse =
  | {
      success: true;
      expiresIn: number;
      resendAvailableIn?: number;
    }
  | {
      success: false;
      error: string;
      message?: string;
      remainingAttempts?: number;
      expiresIn?: number;
      resendAvailableIn?: number;
    };

export type VerifyCodeResponse =
  | {
      success: true;
      verificationToken: string;
      expiresIn: number;
      alreadyRegistered?: boolean;
    }
  | {
      success: false;
      error: string;
      message?: string;
      remainingAttempts?: number;
      expiresIn?: number;
    };

export type SubmitRegistrationResponse =
  | {
      success: true;
      alreadyRegistered?: boolean;
      registeredAt?: string;
    }
  | {
      success: false;
      error: string;
      message?: string;
    };

const STORAGE_KEY = 'bondclaw.registration';

function isRecord(value: unknown): value is Record<string, unknown> {
  return typeof value === 'object' && value !== null;
}

function isString(value: unknown): value is string {
  return typeof value === 'string';
}

function normalizeRegistration(value: unknown): BondClawRegistration | null {
  if (!isRecord(value)) return null;

  const name = isString(value.name) ? value.name.trim() : '';
  const institution = isString(value.institution) ? value.institution.trim() : '';
  const phone = isString(value.phone) ? value.phone.trim() : '';
  const email = isString(value.email) ? value.email.trim() : '';
  const registeredAt = isString(value.registeredAt) ? value.registeredAt : '';

  if (!name || !institution || !phone || !email || !registeredAt) {
    return null;
  }

  const verified = value.verified === true
    || value.verified === 'true'
    || value.verified === 1
    || value.verified === '1';
  const verifiedAt = isString(value.verifiedAt) ? value.verifiedAt : verified ? registeredAt : undefined;
  const version = isString(value.version) ? value.version : 'v2';
  const source = isString(value.source) ? value.source : verified ? 'legacy' : 'pending';

  return {
    name,
    institution,
    phone,
    email,
    registeredAt,
    verified,
    verifiedAt,
    version,
    source,
  };
}

async function requestJson<TResponse>(
  path: string,
  body: Record<string, unknown>,
  init?: RequestInit
): Promise<TResponse> {
  const baseUrl = getBondClawRegistrationApiBaseUrl().replace(/\/$/, '');
  const response = await fetch(`${baseUrl}${path}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...(init?.headers ?? {}),
    },
    body: JSON.stringify(body),
    ...init,
  });

  const text = await response.text();
  let payload: TResponse;
  try {
    payload = JSON.parse(text) as TResponse;
  } catch {
    throw new Error(`Unexpected response from registration API: ${text.slice(0, 200)}`);
  }

  return payload;
}

export function getBondClawRegistration(): BondClawRegistration | null {
  try {
    const raw = localStorage.getItem(STORAGE_KEY);
    if (!raw) return null;
    const parsed = normalizeRegistration(JSON.parse(raw));
    if (!parsed) return null;
    const normalized = JSON.stringify(parsed);
    if (normalized !== raw) {
      localStorage.setItem(STORAGE_KEY, normalized);
    }
    return parsed;
  } catch {
    return null;
  }
}

export function setBondClawRegistration(data: BondClawRegistration): void {
  const normalized = normalizeRegistration(data);
  if (!normalized) {
    throw new Error('Invalid BondClaw registration payload');
  }
  localStorage.setItem(STORAGE_KEY, JSON.stringify(normalized));
}

export function isBondClawRegistered(): boolean {
  const reg = getBondClawRegistration();
  return Boolean(reg?.verified && reg?.name && reg?.institution && reg?.phone && reg?.email);
}

export async function sendVerificationCode(
  email: string
): Promise<SendVerificationCodeResponse> {
  return await requestJson<SendVerificationCodeResponse>('/api/register/send-code', {
    email: email.trim(),
  });
}

export async function verifyCode(
  email: string,
  code: string
): Promise<VerifyCodeResponse> {
  return await requestJson<VerifyCodeResponse>('/api/register/verify-code', {
    email: email.trim(),
    code: code.trim(),
  });
}

export async function submitRegistration(
  data: {
    name: string;
    institution: string;
    phone: string;
    email: string;
    verificationToken: string;
  }
): Promise<SubmitRegistrationResponse> {
  return await requestJson<SubmitRegistrationResponse>('/api/register/submit', {
    ...data,
    name: data.name.trim(),
    institution: data.institution.trim(),
    phone: data.phone.trim(),
    email: data.email.trim(),
    verificationToken: data.verificationToken.trim(),
  });
}
