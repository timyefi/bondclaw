/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { EventEmitter } from 'events';
import { Writable, PassThrough } from 'stream';

/**
 * Create a fake ChildProcess for testing ACP connections.
 *
 * Provides controllable stdin/stdout/stderr streams and lifecycle events.
 * Use `emitStdoutLine()` to simulate JSON-RPC responses from the ACP server.
 */
export function createFakeChildProcess() {
  const stdout = new PassThrough();
  const stderr = new PassThrough();
  const stdin = new Writable({
    write(chunk: Buffer, _encoding: string, callback: () => void) {
      // Capture writes for assertion
      if (stdinListeners.length > 0) {
        for (const listener of stdinListeners) {
          listener(chunk.toString());
        }
      }
      callback();
    },
  });

  const stdinListeners: Array<(data: string) => void> = [];

  const fakeProcess = Object.assign(new EventEmitter(), {
    stdout,
    stderr,
    stdin,
    pid: 12345,
    killed: false,
    kill: () => {
      fakeProcess.killed = true;
      return true;
    },
    unref: () => {},
    ref: () => {},
  });

  return {
    child: fakeProcess as unknown as import('child_process').ChildProcess,
    stdout,
    stderr,
    stdin,
    /** Subscribe to data written to stdin (JSON-RPC requests) */
    onStdinWrite(listener: (data: string) => void) {
      stdinListeners.push(listener);
      return () => {
        const idx = stdinListeners.indexOf(listener);
        if (idx >= 0) stdinListeners.splice(idx, 1);
      };
    },
    /**
     * Emit a JSON-RPC response line on stdout.
     * Automatically adds newline delimiter.
     */
    emitStdoutLine(obj: Record<string, unknown>) {
      stdout.write(JSON.stringify(obj) + '\n');
    },
    /**
     * Emit raw text on stderr.
     */
    emitStderr(text: string) {
      stderr.write(text);
    },
  };
}

export type FakeChildProcessContext = ReturnType<typeof createFakeChildProcess>;
