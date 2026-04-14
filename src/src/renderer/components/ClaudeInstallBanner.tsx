/**
 * ClaudeInstallBanner — Shows a banner prompting to install Claude Code CLI
 * if it's not detected. Provides one-click install with streaming progress.
 */

import { ipcBridge } from '@/common';
import { Alert, Button, Progress } from '@arco-design/web-react';
import React, { useCallback, useEffect, useState } from 'react';
import { useTranslation } from 'react-i18next';

type InstallState = 'checking' | 'not-installed' | 'installing' | 'success' | 'failed';

interface ProgressInfo {
  phase: string;
  attempt: number;
  totalAttempts: number;
  message: string;
  stdout?: string;
  source?: 'bundled' | 'mirror' | 'official';
}

const ClaudeInstallBanner: React.FC = () => {
  const { t } = useTranslation();
  const [state, setState] = useState<InstallState>('checking');
  const [errorMsg, setErrorMsg] = useState('');
  const [progress, setProgress] = useState<ProgressInfo | null>(null);

  const checkInstalled = useCallback(async () => {
    try {
      const installed = await ipcBridge.shell.checkClaudeInstalled.invoke();
      setState(installed ? 'success' : 'not-installed');
    } catch {
      setState('not-installed');
    }
  }, []);

  useEffect(() => {
    void checkInstalled();
  }, [checkInstalled]);

  // Listen for install progress events
  useEffect(() => {
    const unsub = ipcBridge.shell.installProgress.on((event: ProgressInfo) => {
      setProgress(event);
    });
    return unsub;
  }, []);

  const handleInstall = useCallback(async () => {
    setState('installing');
    setErrorMsg('');
    setProgress(null);
    try {
      const result = await ipcBridge.shell.installClaude.invoke();
      if (result.success) {
        setState('success');
      } else {
        setState('failed');
        setErrorMsg(result.error || t('claude.installFailed', { defaultValue: 'Installation failed' }));
      }
    } catch (error) {
      setState('failed');
      setErrorMsg(error instanceof Error ? error.message : String(error));
    }
  }, [t]);

  // Don't render anything if installed or still checking
  if (state === 'success' || state === 'checking') {
    return null;
  }

  if (state === 'installing') {
    const percent = progress
      ? progress.phase === 'done'
        ? 100
        : progress.phase === 'verifying'
          ? 90
          : progress.phase === 'writing_path'
            ? 80
            : progress.phase === 'seeding_bundled'
              ? 35
              : progress.phase === 'installing_mirror' || progress.phase === 'installing_official'
                ? 60
                : Math.round(((progress.attempt - 1) / progress.totalAttempts) * 20)
      : 0;

    return (
      <div className='px-16px py-8px'>
        <Alert
          type='info'
          content={
            <div className='flex flex-col gap-8px'>
              <div className='flex items-center gap-12px'>
                <span>{t('claude.installing', { defaultValue: '正在安装 Claude Code CLI...' })}</span>
                {progress && (
                  <span className='text-12px text-t-3'>
                    ({progress.attempt}/{progress.totalAttempts}
                    {progress.source ? `, ${progress.source}` : ''})
                  </span>
                )}
              </div>
              <Progress percent={percent} size='small' showText={false} />
              {progress?.message && (
                <div className='text-12px text-t-3 truncate max-w-600px' title={progress.message}>
                  {progress.message}
                </div>
              )}
            </div>
          }
        />
      </div>
    );
  }

  if (state === 'failed') {
    return (
      <div className='px-16px py-8px'>
        <Alert
          type='error'
          content={
            <div className='flex items-center justify-between gap-12px'>
              <div>
                <span>{t('claude.installFailed', { defaultValue: 'Claude Code 安装失败' })}</span>
                {errorMsg && <span className='ml-8px text-12px text-t-3'>({errorMsg})</span>}
              </div>
              <Button type='primary' size='small' onClick={() => void handleInstall()}>
                {t('claude.retry', { defaultValue: '重试' })}
              </Button>
            </div>
          }
        />
      </div>
    );
  }

  // not-installed
  return (
    <div className='px-16px py-8px'>
      <Alert
        type='warning'
        content={
          <div className='flex items-center justify-between gap-12px'>
            <div>
              <span className='font-500'>
                {t('claude.notInstalled', {
                  defaultValue: 'Claude Code CLI 未安装',
                })}
              </span>
              <span className='ml-8px text-t-secondary text-13px'>
                {t('claude.requiredNote', {
                  defaultValue: '这是 BondClaw 代理功能的核心依赖，安装后才能使用全部助手功能',
                })}
              </span>
            </div>
            <Button type='primary' size='small' onClick={() => void handleInstall()}>
              {t('claude.oneClickInstall', { defaultValue: '一键安装' })}
            </Button>
          </div>
        }
      />
    </div>
  );
};

export default ClaudeInstallBanner;
