/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useCallback, useState } from 'react';
import { Button, Input, Space } from '@arco-design/web-react';
import { setBondClawRegistration } from '@/common/config/bondclawRegistration';

interface RegistrationGateProps {
  onComplete: () => void;
}

const RegistrationGate: React.FC<RegistrationGateProps> = ({ onComplete }) => {
  const [name, setName] = useState('');
  const [institution, setInstitution] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');

  const canSubmit = name.trim() && institution.trim() && phone.trim() && email.trim();

  const handleSubmit = useCallback(() => {
    if (!canSubmit) return;
    setBondClawRegistration({
      name: name.trim(),
      institution: institution.trim(),
      phone: phone.trim(),
      email: email.trim(),
      registeredAt: new Date().toISOString(),
    });
    onComplete();
  }, [name, institution, phone, email, canSubmit, onComplete]);

  return (
    <div className='fixed inset-0 z-[9999] flex items-center justify-center bg-[linear-gradient(180deg,#f8fafc_0%,#eef2ff_45%,#f8fafc_100%)]'>
      <div className='pointer-events-none absolute inset-x-0 top-0 -z-10 h-320px bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.24),transparent_34%),radial-gradient(circle_at_top_right,rgba(15,23,42,0.18),transparent_30%)]' />
      <div className='w-full max-w-480px rounded-28px border border-slate-200 bg-white/92 p-32px shadow-[0_28px_72px_rgba(15,23,42,0.20)] backdrop-blur-md'>
        <div className='space-y-20px'>
          <div>
            <div className='text-12px font-700 uppercase tracking-[0.18em] text-slate-400'>欢迎使用</div>
            <div className='mt-8px text-28px font-700 text-slate-900'>BondClaw</div>
            <div className='mt-6px text-14px text-slate-500'>国投固收 张亮/叶青 出品</div>
            <div className='mt-8px text-13px leading-6 text-slate-500'>
              请填写您的基本信息以开始使用。我们将通过销售团队为您提供更好的服务。
            </div>
          </div>

          <div className='space-y-12px'>
            <div>
              <div className='mb-4px text-13px font-600 text-slate-700'>
                姓名 <span className='text-red-500'>*</span>
              </div>
              <Input placeholder='请输入您的姓名' value={name} onChange={setName} />
            </div>
            <div>
              <div className='mb-4px text-13px font-600 text-slate-700'>
                机构 <span className='text-red-500'>*</span>
              </div>
              <Input placeholder='请输入您所在的机构名称' value={institution} onChange={setInstitution} />
            </div>
            <div>
              <div className='mb-4px text-13px font-600 text-slate-700'>
                手机号 <span className='text-red-500'>*</span>
              </div>
              <Input placeholder='请输入您的手机号' value={phone} onChange={setPhone} />
            </div>
            <div>
              <div className='mb-4px text-13px font-600 text-slate-700'>
                邮箱 <span className='text-red-500'>*</span>
              </div>
              <Input placeholder='请输入您的邮箱地址' value={email} onChange={setEmail} />
            </div>
          </div>

          <Space direction='vertical' className='w-full' size={12}>
            <Button type='primary' long size='large' disabled={!canSubmit} onClick={handleSubmit}>
              开始使用
            </Button>
            <div className='text-center text-11px text-slate-400'>
              您的信息仅用于身份识别和服务对接，不会用于其他用途。
            </div>
          </Space>
        </div>
      </div>
    </div>
  );
};

export default RegistrationGate;
