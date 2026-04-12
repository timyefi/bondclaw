/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * AcpConnection API Surface Test
 *
 * This test has two purposes:
 * 1. Compile-time check: The Pick type below will fail to compile if any
 *    method is removed from AcpConnection (e.g., swallowed into a JSDoc comment
 *    due to a missing comment closure). Running tsc --noEmit catches this.
 * 2. Runtime check: The it() block verifies at runtime that all required
 *    methods exist on AcpConnection.prototype as functions.
 *
 * This directly prevents the regression where a missing JSDoc closure
 * caused newSession to disappear from the class, leading to the runtime error:
 * "this.connection.newSession is not a function".
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

// ── Compile-time check ──────────────────────────────────────────────
// If any method listed here is removed from AcpConnection, TypeScript
// will report "Type 'X' is not assignable to type 'Pick<...>'" and
// `tsc --noEmit` will fail.
import type { AcpConnection } from '@process/agent/acp/AcpConnection';

type RequiredPublicMethods = Pick<
  AcpConnection,
  | 'connect'
  | 'newSession'
  | 'sendPrompt'
  | 'cancelPrompt'
  | 'disconnect'
  | 'authenticate'
  | 'loadSession'
  | 'setSessionMode'
  | 'setModel'
  | 'setConfigOption'
  | 'getConfigOptions'
  | 'getModels'
  | 'setPromptTimeout'
  | 'getInitializeResponse'
  | 'isConnected'
  | 'hasActiveSession'
  | 'currentSessionId'
  | 'currentBackend'
>;

// This assignment forces TypeScript to verify the Pick type resolves correctly.
// If any method name in RequiredPublicMethods does not exist on AcpConnection,
// the Pick will fail at compile time.
const _typeCheck: RequiredPublicMethods = null as unknown as RequiredPublicMethods;
void _typeCheck;

// ── Runtime check ───────────────────────────────────────────────────

describe('AcpConnection API surface', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    // Mock Electron and Node.js built-in modules that AcpConnection imports
    vi.doMock('electron', () => ({}));
    vi.doMock('child_process', () => ({
      spawn: vi.fn(),
      execFile: vi.fn(),
    }));
    vi.doMock('fs', () => ({
      promises: {
        rm: vi.fn(),
      },
    }));
    vi.doMock('os', () => ({
      homedir: vi.fn(() => '/home/test'),
      platform: vi.fn(() => 'linux'),
    }));
    vi.doMock('path', () => ({
      isAbsolute: vi.fn((p: string) => p.startsWith('/')),
      join: vi.fn((...args: string[]) => args.join('/')),
      resolve: vi.fn((p: string) => p),
      relative: vi.fn(() => ''),
    }));
    vi.doMock('util', () => ({
      promisify: vi.fn((fn: unknown) => fn),
    }));
  });

  afterEach(() => {
    vi.doUnmock('electron');
    vi.doUnmock('child_process');
    vi.doUnmock('fs');
    vi.doUnmock('os');
    vi.doUnmock('path');
    vi.doUnmock('util');
  });

  it('should expose all required public methods on the prototype', async () => {
    const { AcpConnection } = await import('@process/agent/acp/AcpConnection');

    const requiredMethods = [
      'connect',
      'newSession',
      'sendPrompt',
      'cancelPrompt',
      'disconnect',
      'authenticate',
      'loadSession',
      'setSessionMode',
      'setModel',
      'setConfigOption',
      'getConfigOptions',
      'getModels',
      'setPromptTimeout',
      'getInitializeResponse',
    ] as const;

    for (const method of requiredMethods) {
      expect(typeof AcpConnection.prototype[method], `AcpConnection.prototype.${method} should be a function`).toBe(
        'function'
      );
    }
  });

  it('should expose isConnected and hasActiveSession as getters', async () => {
    const { AcpConnection } = await import('@process/agent/acp/AcpConnection');

    const proto = AcpConnection.prototype;
    const isConnectedDesc = Object.getOwnPropertyDescriptor(proto, 'isConnected');
    const hasActiveSessionDesc = Object.getOwnPropertyDescriptor(proto, 'hasActiveSession');
    const currentSessionIdDesc = Object.getOwnPropertyDescriptor(proto, 'currentSessionId');
    const currentBackendDesc = Object.getOwnPropertyDescriptor(proto, 'currentBackend');

    // These should be getter properties (defined via `get isConnected()`)
    expect(typeof isConnectedDesc?.get, 'isConnected should be a getter').toBe('function');
    expect(typeof hasActiveSessionDesc?.get, 'hasActiveSession should be a getter').toBe('function');
    expect(typeof currentSessionIdDesc?.get, 'currentSessionId should be a getter').toBe('function');
    expect(typeof currentBackendDesc?.get, 'currentBackend should be a getter').toBe('function');
  });
});
