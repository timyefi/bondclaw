/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useMemo, useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { Alert, Button, Card, Divider, Message, Select, Space, Spin, Tag, Typography } from '@arco-design/web-react';
import { ArrowRight, Refresh, Book, BellRing, Down, Up } from '@icon-park/react';
import { ipcBridge } from '@/common';
import { ConfigStorage } from '@/common/config/storage';
import type { TProviderWithModel, IProvider } from '@/common/config/storage';
import { buildAgentConversationParams } from '@/common/utils/buildAgentConversationParams';
import { useBondClawRuntimeState } from '@/renderer/hooks/system/useBondClawRuntimeState';
import {
  useBondClawWorkspaceQuery,
  useBondClawWorkspaceSnapshot,
} from '@/renderer/hooks/system/useBondClawWorkspaceSnapshot';
import { openExternalUrl } from '@/renderer/utils/platform';
import SupportRibbon from './components/SupportRibbon';
import ResearchReportsList from './components/ResearchReportsList';

const { Title, Paragraph, Text } = Typography;

const BondClawWorkspacePage: React.FC = () => {
  const runtimeState = useBondClawRuntimeState();
  const navigate = useNavigate();
  const query = useBondClawWorkspaceQuery();
  const { snapshot, loading, error, refresh } = useBondClawWorkspaceSnapshot(query);
  const [expandedRoleId, setExpandedRoleId] = useState<string | null>(null);

  const templateCenter = snapshot?.templateCenter;
  const researchBrain = snapshot?.researchBrain;
  const roleCards = templateCenter?.role_cards || [];
  const selectedPromptPack = templateCenter?.selected_prompt?.prompt_pack || {};

  // Select options
  const roleOptions = roleCards.map((card: Record<string, any>) => ({
    label: card.display_name || card.role_id,
    value: String(card.role_id || ''),
  }));
  const topicOptions = (researchBrain?.filters?.available_topics || []).map((topic: string) => ({
    label: topic,
    value: topic,
  }));

  // Navigation helpers
  const updateQuery = (patch: Partial<Record<'role' | 'topic' | 'case', string | undefined>>) => {
    const next = new URLSearchParams(window.location.search);
    const setParam = (key: string, value?: string) => {
      if (value) next.set(key, value);
      else next.delete(key);
    };
    setParam('role', patch.role);
    setParam('topic', patch.topic);
    setParam('case', patch.case);
    void navigate({ pathname: '/bondclaw', search: next.toString() ? `?${next.toString()}` : '' }, { replace: true });
  };

  const scrollToSection = (sectionId: string) => {
    document.getElementById(sectionId)?.scrollIntoView({ behavior: 'smooth', block: 'start' });
  };

  // Workflow launch
  const handleStartWorkflow = async (roleId: string, promptName: string) => {
    const promptPack = templateCenter?.selected_prompt?.prompt_pack;
    if (!promptPack?.prompt_template) {
      Message.warning('请先选择角色和模板');
      return;
    }

    try {
      const lastAgentKey = await ConfigStorage.get('guid.lastSelectedAgent');
      const backend = lastAgentKey?.split(':')[0] || 'claude';
      const type = backend === 'gemini' ? 'gemini' : backend === 'aionrs' ? 'aionrs' : 'acp';
      let model: TProviderWithModel;
      if (type === 'aionrs') {
        const providers = await ConfigStorage.get('model.config');
        const enabled = providers?.find((p: IProvider) => p.enabled !== false);
        if (!enabled) {
          Message.warning('请先在设置中配置 AI 服务商');
          return;
        }
        const enabledModel = enabled.model?.find((m: string) => enabled.modelEnabled?.[m] !== false);
        model = {
          id: enabled.id,
          platform: enabled.platform,
          name: enabled.name,
          baseUrl: enabled.baseUrl,
          apiKey: enabled.apiKey,
          useModel: enabledModel || enabled.model?.[0] || 'default',
        };
      } else if (type === 'gemini') {
        model = {
          id: 'gemini-placeholder',
          name: 'Gemini',
          useModel: 'default',
          platform: 'gemini-with-google-auth' as TProviderWithModel['platform'],
          baseUrl: '',
          apiKey: '',
        };
      } else {
        model = {} as TProviderWithModel;
      }

      const params = buildAgentConversationParams({
        backend,
        name: `${roleId} — ${promptName}`,
        workspace: '',
        model,
        isPreset: true,
        presetAgentType: backend,
        presetResources: {
          rules: promptPack.prompt_template,
          enabledSkills: ['research-writing', `bondclaw-${roleId}-${promptName}`],
        },
      });

      const conversation = await ipcBridge.conversation.create.invoke(params);
      if (conversation?.id) {
        navigate(`/conversation/${conversation.id}`);
      }
    } catch (err) {
      console.error('[BondClaw] Failed to start workflow:', err);
      Message.error('工作流启动失败，请检查配置');
    }
  };

  const toggleRoleExpand = (roleId: string) => {
    setExpandedRoleId((prev) => (prev === roleId ? null : roleId));
  };

  const handleSelectPrompt = (roleId: string, promptName: string) => {
    updateQuery({ role: roleId, topic: undefined, case: undefined });
  };

  return (
    <div className='flex h-full min-h-0 flex-col overflow-auto bg-1 text-1'>
      <SupportRibbon />

      <div className='mx-auto w-full max-w-[1400px] px-16px py-16px sm:px-24px lg:px-32px'>
        {/* Header */}
        <div className='flex flex-col gap-16px sm:flex-row sm:items-end sm:justify-between'>
          <div>
            <div className='mb-8px flex flex-wrap items-center gap-8px'>
              <Tag color='arcoblue'>{runtimeState.brand.teamLabel}</Tag>
              <Tag color='gray'>{runtimeState.source.toUpperCase()}</Tag>
            </div>
            <Title heading={2} className='!m-0 !text-24px sm:!text-28px'>
              资源中心
            </Title>
            <Paragraph className='!mt-6px !mb-0 text-2 text-14px'>
              提供投研所需技能库以及国投固收研究内容，从研究到执行一站式服务
            </Paragraph>
          </div>
          <Space wrap>
            <Button icon={<Refresh theme='outline' size='16' fill='currentColor' />} onClick={() => void refresh()}>
              刷新
            </Button>
            <Button
              type='primary'
              icon={<Book theme='outline' size='16' fill='currentColor' />}
              onClick={() => void navigate('/bondclaw?role=macro')}
            >
              默认宏观模板
            </Button>
            <Button
              icon={<BellRing theme='outline' size='16' fill='currentColor' />}
              onClick={() => void openExternalUrl(runtimeState.brand.docsBaseUrl).catch(() => {})}
            >
              查看文档
            </Button>
          </Space>
        </div>

        {/* Quick Filters */}
        <Card className='mt-16px rd-16px' bordered>
          <div className='flex flex-col gap-12px sm:flex-row sm:items-center'>
            <div className='flex-1'>
              <div className='mb-6px text-12px text-3'>角色</div>
              <Select
                allowClear
                className='w-full sm:!w-200px'
                placeholder='选择角色'
                value={query.role}
                options={roleOptions}
                onChange={(value) => updateQuery({ role: value || undefined })}
              />
            </div>
            <div className='flex-1'>
              <div className='mb-6px text-12px text-3'>主题</div>
              <Select
                allowClear
                className='w-full sm:!w-200px'
                placeholder='选择主题'
                value={query.topic}
                options={topicOptions}
                onChange={(value) => updateQuery({ topic: value || undefined })}
              />
            </div>
            <Divider type='vertical' className='!hidden sm:!block !mx-8px' />
            <Space size={8}>
              <Button size='small' onClick={() => void navigate('/bondclaw?role=macro')}>
                默认角色
              </Button>
              <Button size='small' onClick={() => void navigate('/bondclaw?role=macro&topic=policy')}>
                政策视图
              </Button>
            </Space>
          </div>
        </Card>

        {/* Main content area */}
        <div className='mt-16px space-y-16px'>
          {/* Template Center */}
          <div id='bondclaw-section-template' className='scroll-mt-24px'>
            <Card
              className='rd-16px'
              title={
                <div>
                  <div className='text-16px font-600'>技能中心</div>
                  <div className='mt-2px text-12px text-3'>点击角色卡片展开查看模板</div>
                </div>
              }
              extra={
                <Space size={12}>
                  <Tag color='arcoblue'>{templateCenter?.header?.role_count ?? 0} 角色</Tag>
                  <Tag color='arcoblue'>{templateCenter?.header?.workflow_count ?? 0} 工作流</Tag>
                  <Tag color='arcoblue'>{templateCenter?.header?.sample_count ?? 0} 样例</Tag>
                </Space>
              }
            >
              <div className='space-y-8px'>
                {roleCards.map((card: Record<string, any>) => {
                  const isExpanded = expandedRoleId === card.role_id;
                  const isSelected = query.role === card.role_id;
                  return (
                    <div
                      key={card.role_id}
                      className={`rd-12px b-1 b-solid transition-colors ${
                        isSelected
                          ? 'b-[rgba(var(--primary-6),0.4)] bg-[rgba(var(--primary-6),0.06)]'
                          : 'b-border-2 bg-1 hover:bg-fill-2'
                      }`}
                    >
                      {/* Role card header — always visible */}
                      <div
                        className='flex items-center justify-between gap-8px px-14px py-10px cursor-pointer'
                        onClick={() => toggleRoleExpand(card.role_id)}
                      >
                        <div className='flex items-center gap-8px flex-1 min-w-0'>
                          <div className='font-600 text-1 truncate'>{card.display_name}</div>
                          <div className='text-12px text-3'>{card.role_id}</div>
                        </div>
                        <div className='flex items-center gap-8px shrink-0'>
                          <Tag color={card.selected ? 'arcoblue' : 'gray'}>{card.prompt_count} 模板</Tag>
                          <span className='text-3 text-12px'>
                            {card.workflow_count} 工作流 · {card.sample_count} 样例
                          </span>
                          {isExpanded ? (
                            <Up theme='outline' size='14' className='text-3' />
                          ) : (
                            <Down theme='outline' size='14' className='text-3' />
                          )}
                        </div>
                      </div>

                      {/* Expanded content — templates for this role */}
                      {isExpanded && (
                        <div className='px-14px pb-14px space-y-8px'>
                          <div className='text-12px text-3 mb-6px'>
                            技能: {card.canonical_skill || 'research-writing'}
                          </div>

                          {/* Prompt/template list */}
                          {(card.prompt_preview || []).length > 0 ? (
                            <div className='grid gap-6px sm:grid-cols-2'>
                              {(card.prompt_preview || []).map((promptName: string) => {
                                const isActive =
                                  query.role === card.role_id &&
                                  templateCenter?.selected_prompt?.prompt_name === promptName;
                                return (
                                  <div
                                    key={promptName}
                                    className={`rd-8px px-12px py-8px b-1 b-solid cursor-pointer transition-colors ${
                                      isActive
                                        ? 'b-[rgba(var(--primary-6),0.5)] bg-[rgba(var(--primary-6),0.08)]'
                                        : 'b-border-2 bg-bg-1 hover:bg-fill-2'
                                    }`}
                                    onClick={(e) => {
                                      e.stopPropagation();
                                      handleSelectPrompt(card.role_id, promptName);
                                    }}
                                  >
                                    <div className='flex items-center gap-6px'>
                                      <Tag size='small' color={isActive ? 'arcoblue' : 'gray'}>
                                        {promptName}
                                      </Tag>
                                      {isActive && <span className='text-11px text-primary'>当前</span>}
                                    </div>
                                  </div>
                                );
                              })}
                            </div>
                          ) : (
                            <div className='text-12px text-3'>暂无模板</div>
                          )}

                          {/* Workflow launch for this role */}
                          <div className='flex justify-end gap-8px pt-4px'>
                            <Button
                              size='small'
                              type='text'
                              onClick={(e) => {
                                e.stopPropagation();
                                updateQuery({ role: card.role_id, topic: undefined, case: undefined });
                              }}
                            >
                              设为当前角色
                            </Button>
                            <Button
                              size='small'
                              type='primary'
                              onClick={(e) => {
                                e.stopPropagation();
                                void handleStartWorkflow(
                                  card.role_id,
                                  templateCenter?.selected_prompt?.prompt_name ||
                                    templateCenter?.default_context?.default_prompt_name ||
                                    'daily-brief'
                                );
                              }}
                            >
                              启动工作流
                            </Button>
                          </div>
                        </div>
                      )}
                    </div>
                  );
                })}

                {roleCards.length === 0 && !loading && (
                  <div className='py-16px text-center text-12px text-3'>暂无角色模板数据</div>
                )}
              </div>

              {/* Current template summary */}
              {templateCenter?.selected_prompt?.prompt_name && (
                <div className='mt-12px rd-12px b-1 b-solid b-border-2 bg-bg-1 px-14px py-10px'>
                  <div className='text-12px text-3'>当前模板</div>
                  <div className='mt-4px font-600 text-1'>{templateCenter.selected_prompt.prompt_name}</div>
                  {templateCenter.selected_prompt.prompt_pack?.prompt_template && (
                    <div className='mt-4px text-13px text-2 leading-6 line-clamp-3'>
                      {templateCenter.selected_prompt.prompt_pack.prompt_template.slice(0, 300)}...
                    </div>
                  )}
                </div>
              )}
            </Card>
          </div>

          {/* Research Reports */}
          <section id='bondclaw-section-research' className='scroll-mt-24px'>
            <Card
              className='rd-16px'
              title={
                <div>
                  <div className='text-16px font-600'>研究报告</div>
                  <div className='mt-2px text-12px text-3'>来自团队的最新研究成果</div>
                </div>
              }
              extra={<Tag color='arcoblue'>{researchBrain?.header?.case_count ?? 0} 条案例</Tag>}
            >
              <ResearchReportsList />
            </Card>
          </section>

          {/* Error state */}
          {error && (
            <Alert
              type='error'
              title='加载失败'
              content={error}
              action={
                <Button type='text' size='small' onClick={() => void refresh()}>
                  重试
                </Button>
              }
            />
          )}

          {/* Loading state */}
          {loading && !snapshot && (
            <div className='flex min-h-[200px] items-center justify-center rd-16px b-1 b-solid b-border-2 bg-1'>
              <Spin size={32} />
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default BondClawWorkspacePage;
