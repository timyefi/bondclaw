/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { AcpAdapter } from '@process/agent/acp/AcpAdapter';
import type { AcpSessionUpdate } from '@/common/types/acpTypes';

const CONVERSATION_ID = 'test-conv-123';
const BACKEND = 'claude';

function makeAgentMessageChunk(text: string): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'agent_message_chunk',
      content: { type: 'text', text },
    },
  } as AcpSessionUpdate;
}

function makeAgentThoughtChunk(text: string): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'agent_thought_chunk',
      content: { text },
    },
  } as AcpSessionUpdate;
}

function makeToolCallUpdate(toolCallId: string, title?: string): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'tool_call',
      toolCallId,
      title: title ?? 'Test Tool',
      kind: 'execute',
    },
  } as AcpSessionUpdate;
}

function makeToolCallStatusUpdate(toolCallId: string, status: 'running' | 'completed' | 'failed'): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'tool_call_update',
      toolCallId,
      status,
      content: `Tool ${status}`,
    },
  } as AcpSessionUpdate;
}

function makePlanUpdate(entries: Array<{ text: string; status?: string }>): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'plan',
      entries: entries.map((e) => ({ text: e.text, status: e.status ?? 'pending' })),
    },
  } as AcpSessionUpdate;
}

function makeConfigOptionUpdate(): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'config_option_update',
      configOptions: [],
    },
  } as AcpSessionUpdate;
}

function makeUsageUpdate(): AcpSessionUpdate {
  return {
    sessionId: 'session-1',
    update: {
      sessionUpdate: 'usage_update',
      used: 1000,
      size: 200000,
    },
  } as AcpSessionUpdate;
}

describe('AcpAdapter', () => {
  it('should convert agent_message_chunk to text message', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makeAgentMessageChunk('Hello world'));

    expect(messages).toHaveLength(1);
    expect(messages[0].type).toBe('text');
    expect(messages[0].position).toBe('left');
    const textMsg = messages[0] as { type: 'text'; content: { content: string } };
    expect(textMsg.content.content).toBe('Hello world');
  });

  it('should accumulate multiple chunks under the same msg_id', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    const msgs1 = adapter.convertSessionUpdate(makeAgentMessageChunk('Hello '));
    const msgs2 = adapter.convertSessionUpdate(makeAgentMessageChunk('World'));

    expect(msgs1).toHaveLength(1);
    expect(msgs2).toHaveLength(1);
    // Both chunks should share the same msg_id for accumulation
    expect(msgs1[0].msg_id).toBe(msgs2[0].msg_id);
  });

  it('should ignore agent_message_chunk with no content', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const update = {
      sessionId: 'session-1',
      update: { sessionUpdate: 'agent_message_chunk' as const },
    } as AcpSessionUpdate;

    const messages = adapter.convertSessionUpdate(update);
    expect(messages).toHaveLength(0);
  });

  it('should ignore non-text agent_message_chunk', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const update = {
      sessionId: 'session-1',
      update: {
        sessionUpdate: 'agent_message_chunk' as const,
        content: { type: 'image', data: '...' },
      },
    } as AcpSessionUpdate;

    const messages = adapter.convertSessionUpdate(update);
    expect(messages).toHaveLength(0);
  });

  it('should convert agent_thought_chunk to tips message', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makeAgentThoughtChunk('Thinking...'));

    expect(messages).toHaveLength(1);
    expect(messages[0].type).toBe('tips');
    expect(messages[0].position).toBe('center');
  });

  it('should convert tool_call to acp_tool_call message', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makeToolCallUpdate('tc-1', 'Bash'));

    expect(messages).toHaveLength(1);
    expect(messages[0].type).toBe('acp_tool_call');
    expect(messages[0].msg_id).toBe('tc-1');
  });

  it('should update existing tool call with tool_call_update', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    // First create the tool call
    adapter.convertSessionUpdate(makeToolCallUpdate('tc-1'));

    // Then update it
    const messages = adapter.convertSessionUpdate(makeToolCallStatusUpdate('tc-1', 'completed'));

    expect(messages).toHaveLength(1);
    expect(messages[0].msg_id).toBe('tc-1');
  });

  it('should ignore tool_call_update for unknown tool call id', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    // Update without creating first — should be silently ignored
    const messages = adapter.convertSessionUpdate(makeToolCallStatusUpdate('unknown-tc', 'completed'));

    expect(messages).toHaveLength(0);
  });

  it('should convert plan update to plan message', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(
      makePlanUpdate([
        { text: 'Step 1', status: 'completed' },
        { text: 'Step 2', status: 'pending' },
      ])
    );

    expect(messages).toHaveLength(1);
    expect(messages[0].type).toBe('plan');
  });

  it('should ignore plan update with no entries', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makePlanUpdate([]));

    expect(messages).toHaveLength(0);
  });

  it('should return empty array for config_option_update', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makeConfigOptionUpdate());

    expect(messages).toHaveLength(0);
  });

  it('should return empty array for usage_update', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const messages = adapter.convertSessionUpdate(makeUsageUpdate());

    expect(messages).toHaveLength(0);
  });

  it('should reset message tracking on tool_call so next chunk gets new msg_id', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    const msgs1 = adapter.convertSessionUpdate(makeAgentMessageChunk('Before'));
    adapter.convertSessionUpdate(makeToolCallUpdate('tc-1'));
    const msgs2 = adapter.convertSessionUpdate(makeAgentMessageChunk('After'));

    // The "Before" and "After" chunks should have different msg_ids
    expect(msgs1[0].msg_id).not.toBe(msgs2[0].msg_id);
  });

  it('should merge plan updates within the same turn', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    const msgs1 = adapter.convertSessionUpdate(makePlanUpdate([{ text: 'Step 1', status: 'completed' }]));
    const msgs2 = adapter.convertSessionUpdate(
      makePlanUpdate([
        { text: 'Step 1', status: 'completed' },
        { text: 'Step 2', status: 'in_progress' },
      ])
    );

    // Both plan updates should share the same msg_id for merging
    expect(msgs1[0].msg_id).toBe(msgs2[0].msg_id);
  });

  it('should reset plan tracking for new turn', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);

    // First turn
    adapter.convertSessionUpdate(makePlanUpdate([{ text: 'Turn 1 Step' }]));

    // Simulate new turn
    adapter.resetPlanTracking();

    const msgs2 = adapter.convertSessionUpdate(makePlanUpdate([{ text: 'Turn 2 Step' }]));

    // The new turn should get a new plan msg_id
    expect(msgs2[0].msg_id).not.toBeUndefined();
  });

  it('should handle unknown session update type gracefully', () => {
    const adapter = new AcpAdapter(CONVERSATION_ID, BACKEND);
    const unknownUpdate = {
      sessionId: 'session-1',
      update: { sessionUpdate: 'future_unknown_type' },
    } as unknown as AcpSessionUpdate;

    // Should not throw, just return empty
    const messages = adapter.convertSessionUpdate(unknownUpdate);
    expect(messages).toHaveLength(0);
  });
});
