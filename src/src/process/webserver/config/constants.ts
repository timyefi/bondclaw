/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { WEBUI_DEFAULT_PORT } from '@/common/config/constants';

// CSRF token cookie/header identifiers (shared by server & WebUI)
export const CSRF_COOKIE_NAME = 'csrf-token';
export const CSRF_HEADER_NAME = 'x-csrf-token';

/**
 * Centralized configuration management.
 */
export const AUTH_CONFIG = {
  TOKEN: {
    SESSION_EXPIRY: '24h' as const,
    WEBSOCKET_EXPIRY: '5m' as const,
    COOKIE_MAX_AGE: 30 * 24 * 60 * 60 * 1000,
    WEBSOCKET_TOKEN_MAX_AGE: 5 * 60,
  },
  RATE_LIMIT: {
    LOGIN_MAX_ATTEMPTS: 5,
    REGISTER_MAX_ATTEMPTS: 3,
    WINDOW_MS: 15 * 60 * 1000,
  },
  DEFAULT_USER: {
    USERNAME: 'admin' as const,
  },
  COOKIE: {
    NAME: 'aionui-session' as const,
    OPTIONS: {
      httpOnly: true,
      secure: false,
      sameSite: 'strict' as const,
    },
  },
} as const;

export const WEBSOCKET_CONFIG = {
  HEARTBEAT_INTERVAL: 30000,
  HEARTBEAT_TIMEOUT: 60000,
  CLOSE_CODES: {
    POLICY_VIOLATION: 1008,
    NORMAL_CLOSURE: 1000,
  },
} as const;

export const SERVER_CONFIG = {
  DEFAULT_HOST: '127.0.0.1' as const,
  REMOTE_HOST: '0.0.0.0' as const,
  DEFAULT_PORT: WEBUI_DEFAULT_PORT,
  BODY_LIMIT: '10mb' as const,

  _currentConfig: {
    host: '127.0.0.1' as string,
    port: WEBUI_DEFAULT_PORT as number,
    allowRemote: false as boolean,
  },

  setServerConfig(port: number, allowRemote: boolean): void {
    this._currentConfig.port = port;
    this._currentConfig.host = allowRemote ? '0.0.0.0' : '127.0.0.1';
    this._currentConfig.allowRemote = allowRemote;
  },

  get isRemoteMode(): boolean {
    return this._currentConfig.allowRemote;
  },

  get BASE_URL(): string {
    if (process.env.SERVER_BASE_URL) {
      return process.env.SERVER_BASE_URL;
    }

    const host = this._currentConfig.host === '0.0.0.0' ? '127.0.0.1' : this._currentConfig.host;
    return `http://${host}:${this._currentConfig.port}`;
  },
} as const;

/**
 * Get dynamic cookie options based on HTTPS configuration.
 */
export function getCookieOptions(): {
  httpOnly: boolean;
  secure: boolean;
  sameSite: 'strict' | 'lax' | 'none';
  maxAge?: number;
} {
  const isHttps =
    process.env.AIONUI_HTTPS === 'true' || (process.env.NODE_ENV === 'production' && process.env.HTTPS === 'true');

  return {
    httpOnly: AUTH_CONFIG.COOKIE.OPTIONS.httpOnly,
    secure: isHttps,
    sameSite: SERVER_CONFIG.isRemoteMode && !isHttps ? 'lax' : AUTH_CONFIG.COOKIE.OPTIONS.sameSite,
  };
}

export const SECURITY_CONFIG = {
  HEADERS: {
    FRAME_OPTIONS: 'DENY',
    CONTENT_TYPE_OPTIONS: 'nosniff',
    XSS_PROTECTION: '1; mode=block',
    REFERRER_POLICY: 'strict-origin-when-cross-origin',
    CSP_DEV:
      "default-src 'self'; script-src 'self' 'unsafe-inline' 'unsafe-eval'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; connect-src 'self' ws: wss: blob:; media-src 'self' blob:;",
    CSP_PROD:
      "default-src 'self'; script-src 'self' 'unsafe-inline'; style-src 'self' 'unsafe-inline'; img-src 'self' data: blob: https:; font-src 'self' data:; connect-src 'self' ws: wss: blob:; media-src 'self' blob:;",
  },
  CSRF: {
    COOKIE_NAME: CSRF_COOKIE_NAME,
    HEADER_NAME: CSRF_HEADER_NAME,
    TOKEN_LENGTH: 32,
    COOKIE_OPTIONS: {
      httpOnly: false,
      sameSite: 'strict' as const,
      secure: false,
      path: '/',
    },
  },
} as const;
