/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * Smoke tests for ACP connection — quick local validation without full install.
 *
 * Run with: bun run test:smoke
 *
 * These tests verify:
 * 1. Module import: AcpConnection class has all required methods
 * 2. Bridge package: the npx package resolves correctly
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';

describe('ACP Smoke Tests', () => {
  beforeEach(() => {
    vi.resetModules();
    vi.clearAllMocks();

    vi.doMock('electron', () => ({}));
    vi.doMock('child_process', () => ({
      spawn: vi.fn(),
      execFile: vi.fn(),
    }));
    vi.doMock('fs', () => ({
      promises: { rm: vi.fn(), readFile: vi.fn(), writeFile: vi.fn() },
    }));
    vi.doMock('os', () => ({
      homedir: vi.fn(() => '/home/test'),
      platform: vi.fn(() => 'linux'),
    }));
    vi.doMock('path', () => ({
      isAbsolute: vi.fn((p: string) => p.startsWith('/')),
      join: vi.fn((...args: string[]) => args.join('/')),
      resolve: vi.fn((p: string) => p),
      relative: vi.fn(() => '.'),
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

  describe('Module Import Check', () => {
    it('should import AcpConnection and expose all required methods', async () => {
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

    it('should have isConnected, hasActiveSession, currentSessionId, currentBackend getters', async () => {
      const { AcpConnection } = await import('@process/agent/acp/AcpConnection');

      const proto = AcpConnection.prototype;
      expect(typeof Object.getOwnPropertyDescriptor(proto, 'isConnected')?.get).toBe('function');
      expect(typeof Object.getOwnPropertyDescriptor(proto, 'hasActiveSession')?.get).toBe('function');
      expect(typeof Object.getOwnPropertyDescriptor(proto, 'currentSessionId')?.get).toBe('function');
      expect(typeof Object.getOwnPropertyDescriptor(proto, 'currentBackend')?.get).toBe('function');
    });

    it('should export buildStartupErrorMessage as a standalone function', async () => {
      const { buildStartupErrorMessage } = await import('@process/agent/acp/AcpConnection');
      expect(typeof buildStartupErrorMessage).toBe('function');
    });
  });

  describe('Supporting Modules', () => {
    it('should import ApprovalStore correctly', async () => {
      const { AcpApprovalStore, createAcpApprovalKey } = await import('@process/agent/acp/ApprovalStore');
      expect(typeof AcpApprovalStore).toBe('function');
      expect(typeof createAcpApprovalKey).toBe('function');
    });

    it('should import modelInfo functions correctly', async () => {
      const { buildAcpModelInfo, summarizeAcpModelInfo } = await import('@process/agent/acp/modelInfo');
      expect(typeof buildAcpModelInfo).toBe('function');
      expect(typeof summarizeAcpModelInfo).toBe('function');
    });

    it('should import AcpAdapter correctly', async () => {
      const { AcpAdapter } = await import('@process/agent/acp/AcpAdapter');
      expect(typeof AcpAdapter).toBe('function');
      expect(typeof AcpAdapter.prototype.convertSessionUpdate).toBe('function');
    });
  });
});
