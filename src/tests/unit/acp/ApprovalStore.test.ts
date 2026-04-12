/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { AcpApprovalStore, createAcpApprovalKey } from '@process/agent/acp/ApprovalStore';

describe('AcpApprovalStore', () => {
  it('should store allow_always decisions', () => {
    const store = new AcpApprovalStore();
    const key = { kind: 'execute', title: 'Run command' };

    store.put(key, 'allow_always');

    expect(store.get(key)).toBe('allow_always');
    expect(store.isApprovedForSession(key)).toBe(true);
  });

  it('should NOT store non-allow_always decisions', () => {
    const store = new AcpApprovalStore();
    const key = { kind: 'execute', title: 'Run command' };

    store.put(key, 'reject_once');

    expect(store.get(key)).toBeUndefined();
    expect(store.isApprovedForSession(key)).toBe(false);
  });

  it('should NOT store allow_once decisions', () => {
    const store = new AcpApprovalStore();
    const key = { kind: 'execute', title: 'Run command' };

    store.put(key, 'allow_once');

    expect(store.get(key)).toBeUndefined();
    expect(store.isApprovedForSession(key)).toBe(false);
  });

  it('should track size of stored approvals', () => {
    const store = new AcpApprovalStore();
    expect(store.size).toBe(0);

    store.put({ kind: 'execute', title: 'cmd1' }, 'allow_always');
    expect(store.size).toBe(1);

    store.put({ kind: 'execute', title: 'cmd2' }, 'allow_always');
    expect(store.size).toBe(2);
  });

  it('should overwrite previous decision for same key', () => {
    const store = new AcpApprovalStore();
    const key = { kind: 'execute', title: 'Run command' };

    store.put(key, 'reject_once');
    expect(store.size).toBe(0);

    store.put(key, 'allow_always');
    expect(store.size).toBe(1);
    expect(store.isApprovedForSession(key)).toBe(true);
  });

  it('should clear all cached approvals', () => {
    const store = new AcpApprovalStore();
    store.put({ kind: 'execute', title: 'cmd1' }, 'allow_always');
    store.put({ kind: 'edit', title: 'cmd2' }, 'allow_always');

    expect(store.size).toBe(2);

    store.clear();

    expect(store.size).toBe(0);
    expect(store.isApprovedForSession({ kind: 'execute', title: 'cmd1' })).toBe(false);
  });

  it('should differentiate keys by kind and title', () => {
    const store = new AcpApprovalStore();

    store.put({ kind: 'execute', title: 'npm test' }, 'allow_always');
    store.put({ kind: 'edit', title: 'npm test' }, 'allow_always');

    expect(store.size).toBe(2);
  });

  it('should differentiate keys by command in rawInput', () => {
    const store = new AcpApprovalStore();

    store.put({ kind: 'execute', title: 'run', rawInput: { command: 'npm test' } }, 'allow_always');
    store.put({ kind: 'execute', title: 'run', rawInput: { command: 'npm build' } }, 'allow_always');

    expect(store.size).toBe(2);
    expect(store.isApprovedForSession({ kind: 'execute', title: 'run', rawInput: { command: 'npm test' } })).toBe(true);
    expect(store.isApprovedForSession({ kind: 'execute', title: 'run', rawInput: { command: 'npm build' } })).toBe(
      true
    );
  });

  it('should differentiate keys by path in rawInput', () => {
    const store = new AcpApprovalStore();

    store.put({ kind: 'edit', title: 'write', rawInput: { path: '/a/file.ts' } }, 'allow_always');
    store.put({ kind: 'edit', title: 'write', rawInput: { path: '/b/file.ts' } }, 'allow_always');

    expect(store.size).toBe(2);
  });

  it('should differentiate keys by file_path in rawInput', () => {
    const store = new AcpApprovalStore();

    store.put({ kind: 'read', title: 'read', rawInput: { file_path: '/a/file.ts' } }, 'allow_always');
    store.put({ kind: 'read', title: 'read', rawInput: { file_path: '/b/file.ts' } }, 'allow_always');

    expect(store.size).toBe(2);
  });

  it('should treat same operation with different description as identical', () => {
    const store = new AcpApprovalStore();

    store.put(
      { kind: 'execute', title: 'run', rawInput: { command: 'npm test', description: 'Run tests' } },
      'allow_always'
    );

    // Same command, different description — should be auto-approved
    expect(
      store.isApprovedForSession({
        kind: 'execute',
        title: 'run',
        rawInput: { command: 'npm test', description: 'Run unit tests' },
      })
    ).toBe(true);
  });
});

describe('createAcpApprovalKey', () => {
  it('should create key from tool call data', () => {
    const key = createAcpApprovalKey({
      kind: 'execute',
      title: 'bash',
      rawInput: { command: 'npm test' },
    });

    expect(key.kind).toBe('execute');
    expect(key.title).toBe('bash');
    expect(key.rawInput?.command).toBe('npm test');
  });

  it('should default kind to "unknown" when missing', () => {
    const key = createAcpApprovalKey({ title: 'bash' });
    expect(key.kind).toBe('unknown');
  });

  it('should default title to empty string when missing', () => {
    const key = createAcpApprovalKey({ kind: 'execute' });
    expect(key.title).toBe('');
  });

  it('should handle empty input', () => {
    const key = createAcpApprovalKey({});
    expect(key.kind).toBe('unknown');
    expect(key.title).toBe('');
    expect(key.rawInput).toBeUndefined();
  });
});
