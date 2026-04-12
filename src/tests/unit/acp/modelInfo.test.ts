/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { describe, it, expect } from 'vitest';
import { buildAcpModelInfo, summarizeAcpModelInfo } from '@process/agent/acp/modelInfo';
import type { AcpSessionConfigOption, AcpSessionModels } from '@/common/types/acpTypes';

// Helper to build a configOption with category='model' and type='select'
function makeModelConfigOption(overrides: Partial<AcpSessionConfigOption> = {}): AcpSessionConfigOption {
  return {
    id: 'model-select',
    category: 'model',
    type: 'select',
    currentValue: 'claude-sonnet-4-20250514',
    options: [
      { value: 'claude-sonnet-4-20250514', name: 'Claude Sonnet 4' },
      { value: 'claude-opus-4-20250514', name: 'Claude Opus 4' },
    ],
    ...overrides,
  };
}

describe('buildAcpModelInfo', () => {
  it('should extract model info from configOptions (preferred source)', () => {
    const configOptions = [makeModelConfigOption()];
    const result = buildAcpModelInfo(configOptions, null);

    expect(result).not.toBeNull();
    expect(result!.source).toBe('configOption');
    expect(result!.currentModelId).toBe('claude-sonnet-4-20250514');
    expect(result!.currentModelLabel).toBe('Claude Sonnet 4');
    expect(result!.canSwitch).toBe(true);
    expect(result!.configOptionId).toBe('model-select');
    expect(result!.availableModels).toHaveLength(2);
  });

  it('should fall back to models API when no configOption with category=model', () => {
    const models: AcpSessionModels = {
      currentModelId: 'gpt-4',
      availableModels: [
        { id: 'gpt-4', name: 'GPT-4' },
        { id: 'gpt-3.5-turbo', name: 'GPT-3.5 Turbo' },
      ],
    };

    const result = buildAcpModelInfo([], models);

    expect(result).not.toBeNull();
    expect(result!.source).toBe('models');
    expect(result!.currentModelId).toBe('gpt-4');
    expect(result!.currentModelLabel).toBe('GPT-4');
    expect(result!.canSwitch).toBe(true);
    expect(result!.configOptionId).toBeUndefined();
  });

  it('should prefer configOptions over models API', () => {
    const configOptions = [makeModelConfigOption()];
    const models: AcpSessionModels = {
      currentModelId: 'gpt-4',
      availableModels: [{ id: 'gpt-4', name: 'GPT-4' }],
    };

    const result = buildAcpModelInfo(configOptions, models);

    expect(result!.source).toBe('configOption');
    expect(result!.currentModelId).toBe('claude-sonnet-4-20250514');
  });

  it('should return null when both sources are empty', () => {
    const result = buildAcpModelInfo(null, null);
    expect(result).toBeNull();
  });

  it('should return null when configOptions has no model category', () => {
    const configOptions: AcpSessionConfigOption[] = [{ id: 'other', category: 'other', type: 'boolean' }];
    const result = buildAcpModelInfo(configOptions, null);
    expect(result).toBeNull();
  });

  it('should return null when configOptions is empty array and models is null', () => {
    const result = buildAcpModelInfo([], null);
    expect(result).toBeNull();
  });

  it('should handle configOption with selectedValue fallback', () => {
    const configOptions = [makeModelConfigOption({ currentValue: undefined, selectedValue: 'claude-opus-4-20250514' })];

    const result = buildAcpModelInfo(configOptions, null);

    expect(result!.currentModelId).toBe('claude-opus-4-20250514');
    expect(result!.currentModelLabel).toBe('Claude Opus 4');
  });

  it('should handle single model (canSwitch=false)', () => {
    const configOptions = [
      makeModelConfigOption({
        options: [{ value: 'only-model', name: 'Only Model' }],
      }),
    ];

    const result = buildAcpModelInfo(configOptions, null);

    expect(result!.canSwitch).toBe(false);
    expect(result!.availableModels).toHaveLength(1);
  });

  it('should handle models with modelId instead of id', () => {
    const models: AcpSessionModels = {
      currentModelId: 'model-a',
      availableModels: [{ modelId: 'model-a', name: 'Model A' }],
    };

    const result = buildAcpModelInfo(null, models);

    expect(result!.currentModelId).toBe('model-a');
    expect(result!.availableModels[0].id).toBe('model-a');
  });

  it('should use value as label fallback when name/label missing in configOption', () => {
    const configOptions = [
      makeModelConfigOption({
        currentValue: 'raw-id',
        selectedValue: undefined,
        options: [{ value: 'raw-id' }],
      }),
    ];

    const result = buildAcpModelInfo(configOptions, null);

    expect(result!.currentModelId).toBe('raw-id');
    expect(result!.currentModelLabel).toBe('raw-id');
    expect(result!.availableModels[0].label).toBe('raw-id');
  });
});

describe('summarizeAcpModelInfo', () => {
  it('should summarize null model info', () => {
    const summary = summarizeAcpModelInfo(null);

    expect(summary.source).toBeNull();
    expect(summary.currentModelId).toBeNull();
    expect(summary.currentModelLabel).toBeNull();
    expect(summary.availableModelCount).toBe(0);
    expect(summary.canSwitch).toBe(false);
    expect(summary.sampleModelIds).toEqual([]);
  });

  it('should summarize configOption-sourced model info', () => {
    const modelInfo = buildAcpModelInfo([makeModelConfigOption()], null);
    const summary = summarizeAcpModelInfo(modelInfo);

    expect(summary.source).toBe('configOption');
    expect(summary.currentModelId).toBe('claude-sonnet-4-20250514');
    expect(summary.availableModelCount).toBe(2);
    expect(summary.canSwitch).toBe(true);
    expect(summary.sampleModelIds).toContain('claude-sonnet-4-20250514');
    expect(summary.sampleModelIds).toContain('claude-opus-4-20250514');
  });

  it('should limit sampleModelIds to first 8 models', () => {
    const manyOptions = Array.from({ length: 12 }, (_, i) => ({
      value: `model-${i}`,
      name: `Model ${i}`,
    }));
    const configOptions = [makeModelConfigOption({ options: manyOptions })];

    const modelInfo = buildAcpModelInfo(configOptions, null);
    const summary = summarizeAcpModelInfo(modelInfo);

    expect(summary.availableModelCount).toBe(12);
    expect(summary.sampleModelIds).toHaveLength(8);
  });
});
