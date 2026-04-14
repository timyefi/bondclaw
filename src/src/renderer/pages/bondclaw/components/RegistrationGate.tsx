/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useMemo, useState } from 'react';
import { Button, Input, Space, Typography } from '@arco-design/web-react';
import {
  sendVerificationCode,
  setBondClawRegistration,
  submitRegistration,
  verifyCode,
} from '@/common/config/bondclawRegistration';

interface RegistrationGateProps {
  onComplete: () => void;
}

type Step = 'form' | 'verify' | 'done';

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const maskEmail = (email: string): string => {
  const trimmed = email.trim();
  const [localPart, domain] = trimmed.split('@');
  if (!localPart || !domain) return trimmed;
  if (localPart.length <= 2) {
    return `${localPart[0] ?? '*'}***@${domain}`;
  }
  return `${localPart.slice(0, 1)}***${localPart.slice(-1)}@${domain}`;
};

const formatCountdown = (seconds: number): string => `${Math.max(0, seconds)}s`;

const RegistrationGate: React.FC<RegistrationGateProps> = ({ onComplete }) => {
  const [step, setStep] = useState<Step>('form');
  const [name, setName] = useState('');
  const [institution, setInstitution] = useState('');
  const [phone, setPhone] = useState('');
  const [email, setEmail] = useState('');
  const [verificationCode, setVerificationCode] = useState('');
  const [loadingAction, setLoadingAction] = useState<'send' | 'verify' | null>(null);
  const [message, setMessage] = useState('');
  const [error, setError] = useState('');
  const [cooldownUntil, setCooldownUntil] = useState<number | null>(null);
  const [cooldownRemaining, setCooldownRemaining] = useState(0);

  const trimmedName = name.trim();
  const trimmedInstitution = institution.trim();
  const trimmedPhone = phone.trim();
  const trimmedEmail = email.trim();
  const canSendCode =
    trimmedName.length > 0 &&
    trimmedInstitution.length > 0 &&
    trimmedPhone.length > 0 &&
    EMAIL_RE.test(trimmedEmail) &&
    loadingAction === null;

  const canVerify = verificationCode.trim().length === 6 && loadingAction === null;
  const isCooldownActive = cooldownRemaining > 0;

  const headerText = useMemo(() => {
    if (step === 'form') return '请填写您的基本信息';
    if (step === 'verify') return '请输入邮箱验证码';
    return '注册成功';
  }, [step]);

  useEffect(() => {
    if (!cooldownUntil) {
      setCooldownRemaining(0);
      return;
    }

    const updateCountdown = () => {
      const remaining = Math.max(0, Math.ceil((cooldownUntil - Date.now()) / 1000));
      setCooldownRemaining(remaining);
      if (remaining === 0) {
        setCooldownUntil(null);
      }
    };

    updateCountdown();
    const timer = window.setInterval(updateCountdown, 1000);
    return () => window.clearInterval(timer);
  }, [cooldownUntil]);

  useEffect(() => {
    if (step !== 'done') return;
    const timer = window.setTimeout(() => {
      onComplete();
    }, 1000);
    return () => window.clearTimeout(timer);
  }, [onComplete, step]);

  const resetTransientState = () => {
    setError('');
    setMessage('');
  };

  const handleSendCode = async () => {
    if (!canSendCode) return;

    resetTransientState();
    setLoadingAction('send');
    try {
      const response = await sendVerificationCode(trimmedEmail);
      if (!response.success) {
        setError(response.message || '发送验证码失败，请稍后再试');
        return;
      }

      setStep('verify');
      setVerificationCode('');
      setMessage(`验证码已发送至 ${maskEmail(trimmedEmail)}`);
      const cooldownSeconds = response.resendAvailableIn ?? 60;
      setCooldownUntil(Date.now() + cooldownSeconds * 1000);
    } catch (error) {
      setError(error instanceof Error ? error.message : '发送验证码失败，请检查网络后重试');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleVerifyAndSubmit = async () => {
    if (!canVerify) return;

    resetTransientState();
    setLoadingAction('verify');
    try {
      const verifyResponse = await verifyCode(trimmedEmail, verificationCode.trim());
      if (!verifyResponse.success) {
        setError(
          verifyResponse.message ||
            (verifyResponse.error === 'expired' ? '验证码已过期，请重新发送' : '验证码错误，请重试')
        );
        return;
      }

      const submitResponse = await submitRegistration({
        name: trimmedName,
        institution: trimmedInstitution,
        phone: trimmedPhone,
        email: trimmedEmail,
        verificationToken: verifyResponse.verificationToken,
      });

      if (!submitResponse.success) {
        setError(submitResponse.message || '提交注册失败，请稍后再试');
        return;
      }

      setBondClawRegistration({
        name: trimmedName,
        institution: trimmedInstitution,
        phone: trimmedPhone,
        email: trimmedEmail,
        registeredAt: submitResponse.registeredAt ?? new Date().toISOString(),
        verified: true,
        verifiedAt: new Date().toISOString(),
        version: 'v2',
        source: submitResponse.alreadyRegistered ? 'migration' : 'bondclaw-verify',
      });
      setStep('done');
      setMessage(
        submitResponse.alreadyRegistered ? '已恢复您的注册状态，正在进入应用' : '注册成功，正在进入应用'
      );
    } catch (error) {
      setError(error instanceof Error ? error.message : '验证失败，请检查网络后重试');
    } finally {
      setLoadingAction(null);
    }
  };

  const handleBackToForm = () => {
    resetTransientState();
    setStep('form');
    setVerificationCode('');
  };

  return (
    <div className='fixed inset-0 z-[9999] flex items-center justify-center bg-[linear-gradient(180deg,#f8fafc_0%,#eef2ff_45%,#f8fafc_100%)] px-16px'>
      <div className='pointer-events-none absolute inset-x-0 top-0 -z-10 h-320px bg-[radial-gradient(circle_at_top_left,rgba(59,130,246,0.24),transparent_34%),radial-gradient(circle_at_top_right,rgba(15,23,42,0.18),transparent_30%)]' />
      <div className='w-full max-w-520px rounded-28px border border-slate-200 bg-white/92 p-32px shadow-[0_28px_72px_rgba(15,23,42,0.20)] backdrop-blur-md'>
        <div className='space-y-20px'>
          <div>
            <div className='text-12px font-700 uppercase tracking-[0.18em] text-slate-400'>欢迎使用</div>
            <div className='mt-8px text-28px font-700 text-slate-900'>BondClaw</div>
            <div className='mt-6px text-14px text-slate-500'>国投固收 张亮/叶青 出品</div>
            <div className='mt-8px text-13px leading-6 text-slate-500'>{headerText}</div>
          </div>

          {error ? (
            <div className='rounded-16px border border-red-200 bg-red-50 px-16px py-12px text-13px text-red-700'>
              {error}
            </div>
          ) : null}

          {message ? (
            <div className='rounded-16px border border-emerald-200 bg-emerald-50 px-16px py-12px text-13px text-emerald-700'>
              {message}
            </div>
          ) : null}

          {step === 'form' ? (
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
          ) : null}

          {step === 'verify' ? (
            <div className='space-y-12px'>
              <div className='rounded-16px bg-slate-50 px-16px py-12px text-13px text-slate-600'>
                验证码已发送至 <span className='font-600 text-slate-900'>{maskEmail(trimmedEmail)}</span>
              </div>
              <div>
                <div className='mb-4px text-13px font-600 text-slate-700'>
                  验证码 <span className='text-red-500'>*</span>
                </div>
                <Input
                  placeholder='请输入 6 位验证码'
                  value={verificationCode}
                  onChange={setVerificationCode}
                  maxLength={6}
                />
              </div>
              <div className='flex flex-wrap items-center gap-8px text-12px text-slate-500'>
                <span>验证码有效期 10 分钟</span>
                <span>·</span>
                <span>重新发送 {isCooldownActive ? `(${formatCountdown(cooldownRemaining)})` : ''}</span>
              </div>
            </div>
          ) : null}

          {step === 'done' ? (
            <div className='rounded-20px border border-emerald-200 bg-emerald-50 px-20px py-18px'>
              <div className='text-18px font-700 text-emerald-800'>注册成功</div>
              <div className='mt-6px text-13px leading-6 text-emerald-700'>{message}</div>
              <div className='mt-12px text-12px text-emerald-600'>即将自动进入应用，也可以手动点击下方按钮。</div>
            </div>
          ) : null}

          <Space direction='vertical' className='w-full' size={12}>
            {step === 'form' ? (
              <>
                <Button type='primary' long size='large' disabled={!canSendCode} loading={loadingAction === 'send'} onClick={handleSendCode}>
                  发送验证码
                </Button>
                <div className='text-center text-11px text-slate-400'>
                  您的信息仅用于身份识别和服务对接，不会用于其他用途。
                </div>
              </>
            ) : null}

            {step === 'verify' ? (
              <>
                <Button
                  type='primary'
                  long
                  size='large'
                  disabled={!canVerify}
                  loading={loadingAction === 'verify'}
                  onClick={handleVerifyAndSubmit}
                >
                  验证并完成注册
                </Button>
                <div className='flex flex-col gap-8px sm:flex-row'>
                  <Button
                    long
                    disabled={isCooldownActive || loadingAction !== null}
                    onClick={handleSendCode}
                  >
                    {isCooldownActive ? `重新发送 ${formatCountdown(cooldownRemaining)}` : '重新发送'}
                  </Button>
                  <Button long onClick={handleBackToForm} disabled={loadingAction !== null}>
                    返回修改信息
                  </Button>
                </div>
              </>
            ) : null}

            {step === 'done' ? (
              <Button type='primary' long size='large' onClick={onComplete}>
                开始使用
              </Button>
            ) : null}
          </Space>
        </div>
      </div>
    </div>
  );
};

export default RegistrationGate;
