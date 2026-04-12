/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

/**
 * AcpConnection Protocol-Level Tests
 *
 * Tests the JSON-RPC protocol flow by mocking the ACP connector layer
 * and injecting a fake child process. This verifies:
 * - Method existence (catches the original JSDoc bug)
 * - JSON-RPC message formatting
 * - Response routing to pending requests
 * - Timeout and error handling
 * - Permission pause/resume logic
 */

import { describe, it, expect, vi, beforeEach, afterEach } from 'vitest';
import type { FakeChildProcessContext } from '../../helpers/fakeChildProcess';

// Track the injected fake child process context
let fakeCtx: FakeChildProcessContext;

beforeEach(() => {
  vi.resetModules();
  vi.clearAllMocks();
  fakeCtx = null as unknown as FakeChildProcessContext;
});

afterEach(() => {
  vi.doUnmock('child_process');
  vi.doUnmock('@process/agent/acp/acpConnectors');
  vi.doUnmock('electron');
  vi.doUnmock('fs');
  vi.doUnmock('os');
  vi.doUnmock('path');
  vi.doUnmock('util');
});

async function setupMocks() {
  const { createFakeChildProcess } = await import('../../helpers/fakeChildProcess');
  fakeCtx = createFakeChildProcess();

  // Mock acpConnectors so connectClaude injects our fake child process
  vi.doMock('@process/agent/acp/acpConnectors', () => {
    const { EventEmitter } = require('events');
    return {
      connectClaude: vi.fn(async (_workingDir: string, hooks: { setup: (result: unknown) => Promise<void> }) => {
        await hooks.setup({ child: fakeCtx.child, isDetached: false });
      }),
      connectCodebuddy: vi.fn(async (_workingDir: string, hooks: { setup: (result: unknown) => Promise<void> }) => {
        await hooks.setup({ child: fakeCtx.child, isDetached: false });
      }),
      connectCodex: vi.fn(async (_workingDir: string, hooks: { setup: (result: unknown) => Promise<void> }) => {
        await hooks.setup({ child: fakeCtx.child, isDetached: false });
      }),
      prepareCleanEnv: vi.fn(async () => ({})),
      spawnGenericBackend: vi.fn(async () => ({ child: fakeCtx.child, isDetached: false })),
      createGenericSpawnConfig: vi.fn(() => ({})),
      ACP_PERF_LOG: false,
    };
  });

  // Mock other Node.js builtins
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
}

/**
 * Helper: connect to claude backend and complete initialize handshake.
 * Returns the AcpConnection instance.
 */
async function connectWithInit(): Promise<
  InstanceType<typeof import('@process/agent/acp/AcpConnection').AcpConnection>
> {
  const { AcpConnection } = await import('@process/agent/acp/AcpConnection');
  const conn = new AcpConnection();

  // Start connection (will call connectClaude which uses fake child process)
  const connectPromise = conn.connect('claude', undefined, '/test/workspace');

  // Wait a tick for setupChildProcessHandlers to attach listeners
  await new Promise((resolve) => setTimeout(resolve, 10));

  // Respond to initialize request
  const initResponse = {
    jsonrpc: '2.0',
    id: 0,
    result: {
      protocolVersion: 1,
      capabilities: {},
    },
  };
  fakeCtx.emitStdoutLine(initResponse);

  await connectPromise;
  return conn;
}

describe('AcpConnection Protocol Tests', () => {
  it('should complete connect → initialize handshake', async () => {
    await setupMocks();
    const conn = await connectWithInit();
    expect(conn.isConnected).toBe(true);
    await conn.disconnect();
  });

  it('should send correct initialize request via stdin', async () => {
    await setupMocks();

    const { AcpConnection } = await import('@process/agent/acp/AcpConnection');
    const conn = new AcpConnection();

    const stdinWrites: string[] = [];
    fakeCtx.onStdinWrite((data) => stdinWrites.push(data));

    const connectPromise = conn.connect('claude', undefined, '/test/workspace');

    // Wait for listeners to be attached
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Respond to initialize
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 0,
      result: { protocolVersion: 1, capabilities: {} },
    });

    await connectPromise;

    // Verify the initialize request was sent
    const initMsg = stdinWrites.find((w) => w.includes('"initialize"'));
    expect(initMsg).toBeDefined();
    const parsed = JSON.parse(initMsg!);
    expect(parsed.method).toBe('initialize');
    expect(parsed.params.protocolVersion).toBe(1);
    expect(parsed.params.clientCapabilities.fs.readTextFile).toBe(true);

    await conn.disconnect();
  });

  it('should create session with newSession after connect', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    const stdinWrites: string[] = [];
    fakeCtx.onStdinWrite((data) => stdinWrites.push(data));

    // Start newSession
    const sessionPromise = conn.newSession('/test/workspace');

    // Wait for the request to be sent
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Respond with session info
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: {
        sessionId: 'session-abc',
        modes: [{ id: 'default', name: 'Default' }],
      },
    });

    const result = await sessionPromise;
    expect(result.sessionId).toBe('session-abc');
    expect(conn.hasActiveSession).toBe(true);
    expect(conn.currentSessionId).toBe('session-abc');

    // Verify the request format
    const sessionMsg = stdinWrites.find((w) => w.includes('"session/new"'));
    expect(sessionMsg).toBeDefined();
    const parsed = JSON.parse(sessionMsg!);
    expect(parsed.method).toBe('session/new');
    expect(parsed.params).toBeDefined();

    await conn.disconnect();
  });

  it('should send prompt with session/prompt', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create session first
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-xyz' },
    });
    await sessionPromise;

    const stdinWrites: string[] = [];
    fakeCtx.onStdinWrite((data) => stdinWrites.push(data));

    // Send prompt
    const promptPromise = conn.sendPrompt('What is 2+2?');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Verify request format
    const promptMsg = stdinWrites.find((w) => w.includes('"session/prompt"'));
    expect(promptMsg).toBeDefined();
    const parsed = JSON.parse(promptMsg!);
    expect(parsed.method).toBe('session/prompt');
    expect(parsed.params.sessionId).toBe('session-xyz');
    expect(parsed.params.prompt).toEqual([{ type: 'text', text: 'What is 2+2?' }]);

    // Respond with end_turn
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 2,
      result: { stopReason: 'end_turn' },
    });

    await promptPromise;
    await conn.disconnect();
  });

  it('should throw "No active ACP session" when sending prompt without session', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    await expect(conn.sendPrompt('test')).rejects.toThrow('No active ACP session');
    await conn.disconnect();
  });

  it('should route session/update notifications to callback', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    const updates: unknown[] = [];
    conn.onSessionUpdate = (data) => updates.push(data);

    // Emit a session/update notification (no id → notification)
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      method: 'session/update',
      params: {
        sessionId: 'session-1',
        update: {
          sessionUpdate: 'agent_message_chunk',
          content: { type: 'text', text: 'Hello' },
        },
      },
    });

    // Wait for event loop
    await new Promise((resolve) => setTimeout(resolve, 10));

    expect(updates).toHaveLength(1);
    expect((updates[0] as Record<string, unknown>).update).toBeDefined();

    await conn.disconnect();
  });

  it('should trigger onDisconnect when process exits during runtime', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    const disconnectCalls: Array<{ code: number | null; signal: string | null }> = [];
    conn.onDisconnect = (data) => disconnectCalls.push(data);

    // Simulate process exit
    fakeCtx.child.emit('exit', 1, 'SIGTERM');

    expect(disconnectCalls).toHaveLength(1);
    expect(disconnectCalls[0].code).toBe(1);
    expect(conn.isConnected).toBe(false);
  });

  it('should reject pending requests when process exits during runtime', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create a pending request (sendPrompt with session)
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-1' },
    });
    await sessionPromise;

    // Start a prompt (creates pending request)
    const promptPromise = conn.sendPrompt('test');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Process dies
    fakeCtx.child.emit('exit', 137, 'SIGKILL');

    await expect(promptPromise).rejects.toThrow('exited unexpectedly');
  });

  it('should cancel prompt with session/cancel notification', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create session
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-1' },
    });
    await sessionPromise;

    const stdinWrites: string[] = [];
    fakeCtx.onStdinWrite((data) => stdinWrites.push(data));

    // Start a prompt (don't respond)
    const promptPromise = conn.sendPrompt('test');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Cancel the prompt
    conn.cancelPrompt();

    // Verify session/cancel notification was sent
    const cancelMsg = stdinWrites.find((w) => w.includes('"session/cancel"'));
    expect(cancelMsg).toBeDefined();
    const parsed = JSON.parse(cancelMsg!);
    expect(parsed.method).toBe('session/cancel');
    expect(parsed.params.sessionId).toBe('session-1');

    // The pending prompt should resolve with null
    const result = await promptPromise;
    expect(result).toBeNull();

    await conn.disconnect();
  });

  it('should handle process exit during startup (before init)', async () => {
    await setupMocks();
    const { AcpConnection } = await import('@process/agent/acp/AcpConnection');
    const conn = new AcpConnection();

    const connectPromise = conn.connect('claude', undefined, '/test/workspace');

    // Wait for setupChildProcessHandlers
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Process exits before initialize completes
    fakeCtx.child.emit('exit', 1, null);

    await expect(connectPromise).rejects.toThrow('exited during startup');
  });

  it('should send session/close on disconnect when session exists', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create session
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-1' },
    });
    await sessionPromise;

    const stdinWrites: string[] = [];
    fakeCtx.onStdinWrite((data) => stdinWrites.push(data));

    // Disconnect should try session/close first
    // We need to respond to session/close or it will timeout
    const disconnectPromise = conn.disconnect();
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Verify session/close was attempted
    const closeMsg = stdinWrites.find((w) => w.includes('"session/close"'));
    expect(closeMsg).toBeDefined();

    // Respond to session/close to let disconnect proceed
    const closeIdMatch = closeMsg!.match(/"id":(\d+)/);
    if (closeIdMatch) {
      fakeCtx.emitStdoutLine({
        jsonrpc: '2.0',
        id: parseInt(closeIdMatch[1]),
        result: {},
      });
    }

    await disconnectPromise;
    expect(conn.isConnected).toBe(false);
  });

  it('should collect stderr for diagnostics on startup failure', async () => {
    await setupMocks();
    const { AcpConnection } = await import('@process/agent/acp/AcpConnection');
    const conn = new AcpConnection();

    const connectPromise = conn.connect('claude', undefined, '/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Emit some stderr
    fakeCtx.emitStderr('Error: something went wrong\n');

    // Process exits
    fakeCtx.child.emit('exit', 1, null);

    await expect(connectPromise).rejects.toThrow('something went wrong');
  });

  it('should fire onEndTurn when stopReason is end_turn', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create session
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-1' },
    });
    await sessionPromise;

    let endTurnFired = false;
    conn.onEndTurn = () => {
      endTurnFired = true;
    };

    // Start a prompt
    const promptPromise = conn.sendPrompt('test');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Respond with end_turn
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 2,
      result: { stopReason: 'end_turn' },
    });

    await promptPromise;
    expect(endTurnFired).toBe(true);

    await conn.disconnect();
  });

  it('should fire onPromptUsage when usage is included in response', async () => {
    await setupMocks();
    const conn = await connectWithInit();

    // Create session
    const sessionPromise = conn.newSession('/test/workspace');
    await new Promise((resolve) => setTimeout(resolve, 10));
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 1,
      result: { sessionId: 'session-1' },
    });
    await sessionPromise;

    const usageData: unknown[] = [];
    conn.onPromptUsage = (usage) => usageData.push(usage);

    // Start a prompt
    const promptPromise = conn.sendPrompt('test');
    await new Promise((resolve) => setTimeout(resolve, 10));

    // Respond with usage data
    fakeCtx.emitStdoutLine({
      jsonrpc: '2.0',
      id: 2,
      result: {
        stopReason: 'end_turn',
        usage: {
          inputTokens: 100,
          outputTokens: 50,
          totalTokens: 150,
        },
      },
    });

    await promptPromise;
    expect(usageData).toHaveLength(1);
    expect((usageData[0] as { totalTokens: number }).totalTokens).toBe(150);

    await conn.disconnect();
  });
});
