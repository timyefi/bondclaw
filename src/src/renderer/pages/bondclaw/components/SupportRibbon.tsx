/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useState } from 'react';
import { getBondClawTeamLabel } from '@/common/config/bondclawBrand';

const SupportRibbon: React.FC = () => {
  const [dismissed, setDismissed] = useState(() => {
    return sessionStorage.getItem('bondclaw.ribbonDismissed') === 'true';
  });

  useEffect(() => {
    if (dismissed) {
      sessionStorage.setItem('bondclaw.ribbonDismissed', 'true');
    }
  }, [dismissed]);

  if (dismissed) return null;

  const teamLabel = getBondClawTeamLabel();

  return (
    <div className='relative flex h-32px items-center overflow-hidden rounded-t-16px border-b border-slate-200 bg-[linear-gradient(90deg,rgba(59,130,246,0.06)_0%,rgba(59,130,246,0.02)_50%,rgba(59,130,246,0.06)_100%)]'>
      <div className='pointer-events-none absolute inset-0 flex'>
        <div className='animate-marquee flex items-center whitespace-nowrap'>
          <span className='mx-48px text-12px text-slate-500'>请通过打分支持 {teamLabel}</span>
          <span className='mx-48px text-12px text-slate-400'>感谢您使用 BondClaw — 您的支持是我们持续优化的动力</span>
          <span className='mx-48px text-12px text-slate-500'>请通过打分支持 {teamLabel}</span>
          <span className='mx-48px text-12px text-slate-400'>感谢您使用 BondClaw — 您的支持是我们持续优化的动力</span>
        </div>
      </div>
      <button
        type='button'
        className='absolute right-8px z-10 flex h-20px w-20px items-center justify-center rounded-full text-12px text-slate-400 transition-colors hover:bg-slate-200 hover:text-slate-600'
        onClick={() => setDismissed(true)}
        aria-label='关闭'
      >
        ✕
      </button>
      <style>{`
        @keyframes marquee {
          0% { transform: translateX(0); }
          100% { transform: translateX(-50%); }
        }
        .animate-marquee {
          animation: marquee 30s linear infinite;
        }
      `}</style>
    </div>
  );
};

export default SupportRibbon;
