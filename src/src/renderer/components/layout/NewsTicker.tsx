/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React, { useEffect, useState, useCallback, useRef } from 'react';

const STORAGE_KEY = 'bondclaw.newsTicker.lastShown';
const INTERVAL_MS = 30 * 60 * 1000; // 30 minutes
const AUTO_DISMISS_MS = 5000; // 5 seconds

const MESSAGE = '研究开发不易，请大力支持国投固收 张亮/叶青';

const NewsTicker: React.FC = () => {
  const [visible, setVisible] = useState(false);
  const [fadingOut, setFadingOut] = useState(false);
  const intervalRef = useRef<ReturnType<typeof setInterval>>();

  const show = useCallback(() => {
    setFadingOut(false);
    setVisible(true);
    sessionStorage.setItem(STORAGE_KEY, String(Date.now()));
  }, []);

  const hide = useCallback(() => {
    setFadingOut(true);
    // Wait for fade-out animation before removing
    setTimeout(() => {
      setVisible(false);
      setFadingOut(false);
    }, 400);
  }, []);

  // On mount: show immediately if interval has elapsed (sessionStorage resets on app restart)
  useEffect(() => {
    const lastShown = sessionStorage.getItem(STORAGE_KEY);
    const now = Date.now();
    if (!lastShown || now - Number(lastShown) >= INTERVAL_MS) {
      show();
    }

    // Re-check every 30 minutes
    intervalRef.current = setInterval(() => {
      const last = sessionStorage.getItem(STORAGE_KEY);
      const now = Date.now();
      if (!last || now - Number(last) >= INTERVAL_MS) {
        show();
      }
    }, INTERVAL_MS);

    return () => {
      if (intervalRef.current) clearInterval(intervalRef.current);
    };
  }, [show]);

  // Auto-dismiss after 5 seconds
  useEffect(() => {
    if (!visible || fadingOut) return;
    const timer = setTimeout(hide, AUTO_DISMISS_MS);
    return () => clearTimeout(timer);
  }, [visible, fadingOut, hide]);

  if (!visible) return null;

  return (
    <div
      className={`flex items-center justify-center h-28px px-16px text-12px border-b border-[var(--color-border-2)] transition-opacity duration-400 ${fadingOut ? 'opacity-0' : 'opacity-100'} bg-[rgba(var(--primary-6),0.06)] text-t-secondary`}
    >
      <span className='tracking-wide'>{MESSAGE}</span>
    </div>
  );
};

export default NewsTicker;
