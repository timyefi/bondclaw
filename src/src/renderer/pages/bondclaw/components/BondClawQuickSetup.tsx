/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useCallback, useState } from 'react';
import { Alert, Button, Input, Select, Space, Tag } from '@arco-design/web-react';
import { CheckCorrect, Lock, Unlock } from '@icon-park/react';
import type { IProvider } from '@/common/config/storage';
import { ipcBridge } from '@/common';

/** Pre-configured provider presets for Chinese market */
const PROVIDER_PRESETS = [
  {
    label: '智谱 GLM',
    name: '智谱 GLM',
    baseUrl: 'https://open.bigmodel.cn/api/paas/v4',
    model: 'glm-5.1',
    hint: '推荐 · 国内首选',
  },
  {
    label: '通义千问',
    name: '通义千问 Qwen',
    baseUrl: 'https://dashscope.aliyuncs.com/compatible-mode/v1',
    model: 'qwen3-235b-a22b',
    hint: '阿里云',
  },
  { label: 'DeepSeek', name: 'DeepSeek', baseUrl: 'https://api.deepseek.com/v1', model: 'deepseek-chat', hint: '' },
  { label: 'Kimi', name: 'Kimi', baseUrl: 'https://api.moonshot.cn/v1', model: 'moonshot-v1-auto', hint: '月之暗面' },
  {
    label: '字节豆包',
    name: '字节豆包',
    baseUrl: 'https://ark.cn-beijing.volces.com/api/v3',
    model: 'doubao-1.5-pro-32k',
    hint: '火山引擎',
  },
  { label: '百度文心', name: '百度文心', baseUrl: 'https://qianfan.baidubce.com/v2', model: 'ernie-4.0-8k', hint: '' },
  {
    label: '腾讯混元',
    name: '腾讯混元',
    baseUrl: 'https://api.hunyuan.cloud.tencent.com/v1',
    model: 'hunyuan-turbos',
    hint: '',
  },
  { label: 'MiniMax', name: 'MiniMax', baseUrl: 'https://api.minimaxi.com/v1', model: 'MiniMax-Text-01', hint: '' },
  {
    label: '硅基流动',
    name: '硅基流动',
    baseUrl: 'https://api.siliconflow.cn/v1',
    model: 'deepseek-ai/DeepSeek-V3',
    hint: '聚合平台',
  },
] as const;

interface BondClawQuickSetupProps {
  onConfigured?: () => void;
  /** When true, renders without outer card border/shadow for embedding in Settings */
  compact?: boolean;
}

const BondClawQuickSetup: React.FC<BondClawQuickSetupProps> = ({ onConfigured, compact }) => {
  const [selectedIdx, setSelectedIdx] = useState(0);
  const [apiKey, setApiKey] = useState('');
  const [showKey, setShowKey] = useState(false);
  const [saving, setSaving] = useState(false);
  const [configured, setConfigured] = useState(false);

  const preset = PROVIDER_PRESETS[selectedIdx];

  const handleSave = useCallback(async () => {
    if (!apiKey.trim()) return;

    setSaving(true);
    try {
      const providers: IProvider[] = (await ipcBridge.mode.getModelConfig.invoke()) || [];

      const existingIdx = providers.findIndex((p) => p.name === preset.name);
      const newProvider: IProvider = {
        id: existingIdx >= 0 ? providers[existingIdx].id : `bondclaw-${preset.name}-${Date.now()}`,
        platform: 'custom',
        name: preset.name,
        baseUrl: preset.baseUrl,
        apiKey: apiKey.trim(),
        model: [preset.model],
        enabled: true,
      };

      // Disable all other providers, keep only one active
      const updated = providers.map((p) => ({ ...p, enabled: p.name === preset.name }));

      if (existingIdx >= 0) {
        updated[existingIdx] = newProvider;
      } else {
        updated.push(newProvider);
      }

      const result = await ipcBridge.mode.saveModelConfig.invoke(updated);
      if (result.success) {
        setConfigured(true);
        onConfigured?.();
      }
    } catch (error) {
      console.error('[BondClaw] Failed to save provider config:', error);
    } finally {
      setSaving(false);
    }
  }, [apiKey, preset, onConfigured]);

  const selectOptions = PROVIDER_PRESETS.map((p, idx) => ({
    label: (
      <div className='flex items-center gap-8px'>
        <span>{p.label}</span>
        {p.hint ? (
          <Tag size='small' color='arcoblue'>
            {p.hint}
          </Tag>
        ) : null}
      </div>
    ),
    value: idx,
  }));

  if (configured) {
    return (
      <Alert
        type='success'
        title='AI 服务商已配置'
        content={
          <Space>
            <Tag color='green'>{preset.name}</Tag>
            <span className={compact ? 'text-t-secondary' : 'text-slate-500'}>{preset.model}</span>
          </Space>
        }
        icon={<CheckCorrect theme='filled' size='16' />}
      />
    );
  }

  const content = (
    <div className={compact ? 'space-y-12px' : 'space-y-16px'}>
      {!compact && (
        <>
          <div>
            <div className='text-12px font-700 uppercase tracking-[0.18em] text-slate-400'>AI 服务配置</div>
            <div className='mt-4px text-16px font-700 text-slate-900'>选择服务商，填入 API Key 即可使用</div>
            <div className='mt-4px text-13px text-slate-500'>默认推荐智谱 GLM-5.1。只需两步：选服务商 → 粘贴 Key。</div>
          </div>
        </>
      )}

      <div>
        <div className='mb-6px text-13px font-600 text-t-primary'>选择服务商</div>
        <Select
          className='w-full'
          value={selectedIdx}
          options={selectOptions}
          onChange={(val) => setSelectedIdx(val as number)}
          triggerProps={{ contentStyle: { maxHeight: 320 } }}
        />
        <div className='mt-4px text-12px text-t-secondary'>接口地址：{preset.baseUrl}</div>
      </div>

      <div>
        <div className='mb-6px text-13px font-600 text-t-primary'>API Key</div>
        <div className='flex gap-8px'>
          <Input
            className='flex-1'
            type={showKey ? 'text' : 'password'}
            placeholder='粘贴您的 API Key'
            value={apiKey}
            onChange={setApiKey}
          />
          <Button
            type='secondary'
            icon={showKey ? <Unlock theme='outline' size='16' /> : <Lock theme='outline' size='16' />}
            onClick={() => setShowKey(!showKey)}
          />
        </div>
        <div className='mt-4px text-12px text-t-secondary'>请在对应服务商官网获取 API Key</div>
      </div>

      <div className='flex items-center gap-12px'>
        <Button type='primary' long loading={saving} disabled={!apiKey.trim()} onClick={() => void handleSave()}>
          一键配置
        </Button>
      </div>

      <div className='text-12px text-t-secondary'>
        配置后默认使用 <Tag size='small'>{preset.model}</Tag> 模型。高级配置可在下方展开。
      </div>
    </div>
  );

  if (compact) {
    return content;
  }

  return (
    <div className='rounded-24px border border-slate-200 bg-white p-20px shadow-[0_12px_36px_rgba(15,23,42,0.08)]'>
      {content}
    </div>
  );
};

export default BondClawQuickSetup;
