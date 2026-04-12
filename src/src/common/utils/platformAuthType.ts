/**
 * @license
 * Copyright 2025 BondClaw (github.com/timyefi/bondclaw)
 * SPDX-License-Identifier: Apache-2.0
 */

import { AuthType } from '@office-ai/aioncli-core';
import { isNewApiPlatform } from './platformConstants';

/**
 * 鏍规嵁骞冲彴鍚嶇О鑾峰彇瀵瑰簲鐨勮璇佺被鍨? * @param platform 骞冲彴鍚嶇О
 * @returns 瀵瑰簲鐨凙uthType
 */
export function getAuthTypeFromPlatform(platform: string): AuthType {
  const platformLower = platform?.toLowerCase() || '';

  // Gemini 鐩稿叧骞冲彴
  if (platformLower.includes('gemini-with-google-auth')) {
    return AuthType.LOGIN_WITH_GOOGLE;
  }
  if (platformLower.includes('gemini-vertex-ai') || platformLower.includes('vertex-ai')) {
    return AuthType.USE_VERTEX_AI;
  }
  if (platformLower.includes('gemini') || platformLower.includes('google')) {
    return AuthType.USE_GEMINI;
  }

  // Anthropic/Claude 鐩稿叧骞冲彴
  if (platformLower.includes('anthropic') || platformLower.includes('claude')) {
    return AuthType.USE_ANTHROPIC;
  }

  // AWS Bedrock 骞冲彴
  if (platformLower.includes('bedrock')) {
    return AuthType.USE_BEDROCK;
  }

  // New API gateway defaults to OpenAI compatible (per-model protocol handled by getProviderAuthType)
  // Other platforms default to OpenAI-compatible auth.
  // Includes OpenRouter, OpenAI, DeepSeek, new-api, etc.
  return AuthType.USE_OPENAI;
}
/**
 * 鑾峰彇provider鐨勮璇佺被鍨嬶紝浼樺厛浣跨敤鏄庣‘鎸囧畾鐨刟uthType锛屽惁鍒欐牴鎹畃latform鎺ㄦ柇
 * 瀵逛簬 new-api 骞冲彴锛屾敮鎸佸熀浜庢ā鍨嬪悕绉扮殑鍗忚瑕嗙洊
 * Get provider auth type, prefer explicit authType, otherwise infer from platform
 * For new-api platform, supports per-model protocol overrides
 * @param provider 鍖呭惈platform鍜屽彲閫塧uthType鐨刾rovider閰嶇疆
 * @returns 璁よ瘉绫诲瀷
 */
export function getProviderAuthType(provider: {
  platform: string;
  authType?: AuthType;
  modelProtocols?: Record<string, string>;
  useModel?: string;
}): AuthType {
  // If authType is explicitly provided, use it directly.
  if (provider.authType) {
  }

  // new-api 骞冲彴锛氭牴鎹ā鍨嬪悕绉版煡鎵惧崗璁鐩?  // new-api platform: look up per-model protocol override
  if (isNewApiPlatform(provider.platform) && provider.useModel && provider.modelProtocols) {
    const protocol = provider.modelProtocols[provider.useModel];
    if (protocol) {
      return getAuthTypeFromPlatform(protocol);
    }
  }

  // 鍚﹀垯鏍规嵁platform鎺ㄦ柇
  return getAuthTypeFromPlatform(provider.platform);
}
