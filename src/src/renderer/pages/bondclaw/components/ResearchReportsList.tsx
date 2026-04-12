/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useState } from 'react';
import { Button, Skeleton, Tag } from '@arco-design/web-react';
import useSWR from 'swr';
import { getBondClawResearchFeedUrl } from '@/common/config/bondclawBrand';

type ResearchReport = {
  id: string;
  title: string;
  date: string;
  tags: string[];
  summary: string;
  content_url?: string;
};

type ReportsResponse = {
  reports: ResearchReport[];
};

const fetcher = async (url: string): Promise<ReportsResponse> => {
  try {
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 8000);
    const res = await fetch(url, { signal: controller.signal });
    clearTimeout(timeoutId);
    if (!res.ok) throw new Error(`HTTP ${res.status}`);
    return await res.json();
  } catch {
    return { reports: [] };
  }
};

const TAG_COLORS = ['arcoblue', 'green', 'orange', 'purple', 'cyan'];

const ResearchReportsList: React.FC = () => {
  const feedUrl = getBondClawResearchFeedUrl();
  const { data, isLoading } = useSWR(feedUrl || null, fetcher, {
    revalidateOnFocus: false,
    dedupingInterval: 60000,
  });

  const [expandedId, setExpandedId] = useState<string | null>(null);

  const reports = data?.reports || [];

  // Placeholder demo reports when no endpoint is configured
  const displayReports =
    reports.length > 0
      ? reports
      : [
          {
            id: 'demo-1',
            title: '宏观利率周报：资金面扰动下的债市展望',
            date: '2026-04-11',
            tags: ['宏观', '利率'],
            summary:
              '本周资金面受税期和政府债缴款影响，DR007中枢上行至1.85%附近。央行通过逆回购投放进行对冲，但整体流动性边际收紧。建议关注下周MLF续作规模及LPR报价。',
          },
          {
            id: 'demo-2',
            title: '信用债市场双周报：城投化债进展与信用利差',
            date: '2026-04-09',
            tags: ['信用', '城投'],
            summary:
              '化债政策持续推进，12个重点省份化债方案陆续落地。城投债信用利差整体收窄，但区域分化明显。建议关注江苏、浙江等经济强省的区县级平台配置机会。',
          },
          {
            id: 'demo-3',
            title: '转债市场月报：估值压缩后的布局窗口',
            date: '2026-04-05',
            tags: ['转债', '多资产'],
            summary:
              '3月转债市场跟随正股调整，中证转债指数下跌2.3%。估值压缩至历史中位数附近，双低策略标的增多。建议关注银行、公用事业等防御性品种。',
          },
        ];

  if (isLoading) {
    return (
      <div className='space-y-8px'>
        {[1, 2, 3].map((i) => (
          <Skeleton key={i} text={{ rows: 2 }} animation />
        ))}
      </div>
    );
  }

  return (
    <div className='space-y-8px'>
      <div className='mb-12px flex items-center justify-between'>
        <div>
          <div className='text-12px font-700 uppercase tracking-[0.18em] text-slate-400'>最新研究</div>
          <div className='mt-4px text-14px text-slate-600'>来自国投固收研究团队的最新成果推送</div>
        </div>
        {!feedUrl && <Tag color='orange'>演示数据</Tag>}
      </div>
      {displayReports.map((report) => {
        const isExpanded = expandedId === report.id;
        return (
          <div
            key={report.id}
            className='rounded-16px border border-slate-200 bg-white p-14px transition-all hover:shadow-[0_8px_20px_rgba(15,23,42,0.06)]'
          >
            <div className='flex items-start justify-between gap-12px'>
              <div className='flex-1 min-w-0'>
                <div className='font-600 text-slate-900'>{report.title}</div>
                <div className='mt-6px flex items-center gap-8px'>
                  <span className='text-12px text-slate-400'>{report.date}</span>
                  {(report.tags || []).map((tag, i) => (
                    <Tag key={tag} size='small' color={TAG_COLORS[i % TAG_COLORS.length]}>
                      {tag}
                    </Tag>
                  ))}
                </div>
              </div>
              <Button size='mini' type='text' onClick={() => setExpandedId(isExpanded ? null : report.id)}>
                {isExpanded ? '收起' : '详情'}
              </Button>
            </div>
            {isExpanded && (
              <div className='mt-10px text-13px leading-6 text-slate-600'>
                {report.summary}
                {report.content_url && (
                  <div className='mt-8px'>
                    <a
                      href={report.content_url}
                      target='_blank'
                      rel='noopener noreferrer'
                      className='text-12px text-blue-600 hover:underline'
                    >
                      查看完整报告 →
                    </a>
                  </div>
                )}
              </div>
            )}
          </div>
        );
      })}
      {!feedUrl && (
        <div className='mt-8px rounded-14px border border-dashed border-slate-300 bg-slate-50 p-12px text-center text-12px text-slate-500'>
          研究推送端点尚未配置，当前显示演示数据。配置 researchFeedUrl 后可拉取实时报告。
        </div>
      )}
    </div>
  );
};

export default ResearchReportsList;
