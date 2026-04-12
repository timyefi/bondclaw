/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import React from 'react';
import GeminiModalContent from '@/renderer/components/settings/SettingsModal/contents/GeminiModalContent';
import SettingsPageWrapper from './components/SettingsPageWrapper';

const GeminiSettings: React.FC = () => {
  return (
    <SettingsPageWrapper>
      <GeminiModalContent />
    </SettingsPageWrapper>
  );
};

export default GeminiSettings;
