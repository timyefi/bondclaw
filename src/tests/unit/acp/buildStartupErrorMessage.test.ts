/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { buildStartupErrorMessage } from '@process/agent/acp/AcpConnection';

describe('buildStartupErrorMessage', () => {
  it('should include stderr when present', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, 'Some error output', undefined, null);
    expect(msg).toContain('Some error output');
    expect(msg).toContain('code: 1');
  });

  it('should suggest CLI version issue when code=0 and no stderr', () => {
    const msg = buildStartupErrorMessage('claude', 0, null, '', undefined, null);
    expect(msg).toContain('code: 0');
    expect(msg).toContain('does not support ACP mode');
    expect(msg).toContain('upgrade');
  });

  it('should detect "not recognized" (Windows) and suggest installation', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, "'claude' is not recognized", undefined, 'claude');
    expect(msg).toContain('CLI not found');
    expect(msg).toContain('install');
  });

  it('should detect "command not found" (Unix) and suggest installation', () => {
    const msg = buildStartupErrorMessage('claude', 127, null, '/bin/sh: claude: command not found', undefined, null);
    expect(msg).toContain('CLI not found');
    expect(msg).toContain('install');
  });

  it('should detect "No such file" in stderr', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, 'Error: No such file or directory', undefined, null);
    expect(msg).toContain('CLI not found');
  });

  it('should detect ENOENT in spawnErrorMessage', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, '', 'ENOENT: no such file', null);
    expect(msg).toContain('CLI not found');
  });

  it('should use resolvedBackend as CLI hint when available', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, 'not found', undefined, '/custom/path/claude');
    expect(msg).toContain("'/custom/path/claude' CLI not found");
  });

  it('should fall back to backend name when resolvedBackend is null', () => {
    const msg = buildStartupErrorMessage('claude', 1, null, 'not found', undefined, null);
    expect(msg).toContain("'claude' CLI not found");
  });

  it('should detect config loading errors and provide guidance', () => {
    const msg = buildStartupErrorMessage(
      'codex',
      1,
      null,
      'error loading config: /home/user/.codex/config.toml\nParse error at line 5',
      undefined,
      null
    );
    expect(msg).toContain('config file error');
    expect(msg).toContain('/home/user/.codex/config.toml');
    expect(msg).toContain('review or temporarily rename');
  });

  it('should use generic hint when config path cannot be extracted', () => {
    const msg = buildStartupErrorMessage('codex', 1, null, 'error loading config:', undefined, null);
    expect(msg).toContain('the CLI config file');
  });

  it('should produce basic message for exit with code and signal but no stderr', () => {
    const msg = buildStartupErrorMessage('claude', null, 'SIGTERM', '', undefined, null);
    expect(msg).toContain('code: null');
    expect(msg).toContain('signal: SIGTERM');
  });
});
