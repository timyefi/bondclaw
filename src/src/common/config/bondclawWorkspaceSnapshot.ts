/**
 * @license
 * Copyright 2025 BondClaw
 * SPDX-License-Identifier: Apache-2.0
 */

export type BondClawWorkspaceQuery = {
  role?: string;
  topic?: string;
  caseId?: string;
};

export type BondClawWorkspaceSnapshot = {
  loadedAt: string;
  query: BondClawWorkspaceQuery;
  overview: {
    appName: string;
    teamLabel: string;
    sourceCount: number;
    caseCount: number;
    roleCount: number;
    queueCount: number;
    pendingCount: number;
  };
  settings: {
    header: Record<string, any>;
    summary_cards: Array<Record<string, any>>;
    brand_cards: Array<Record<string, any>>;
    update_cards: Array<Record<string, any>>;
    online_cards: Array<Record<string, any>>;
    quick_actions: Array<Record<string, any>>;
    notes: string[];
  };
  templateCenter: {
    header: Record<string, any>;
    role_cards: Array<Record<string, any>>;
    default_context: Record<string, any>;
    selected_role: Record<string, any>;
    selected_prompt: Record<string, any>;
    recommended_actions: Array<Record<string, any>>;
    notes: string[];
  };
  researchBrain: {
    header: Record<string, any>;
    source_cards: Array<Record<string, any>>;
    source_groups: Array<Record<string, any>>;
    theme_overview: Array<Record<string, any>>;
    case_highlights: Array<Record<string, any>>;
    filters: Record<string, any>;
    case_browser: Record<string, any>;
    case_details: Record<string, any>;
    prompt_shortcuts: Array<Record<string, any>>;
    recommended_actions: Array<Record<string, any>>;
    notes: string[];
  };
  contact: {
    header: Record<string, any>;
    required_fields: string[];
    delivery_order: string[];
    retry_policy: Record<string, any>;
    queue_status: Record<string, any>;
    submission_cards: Array<Record<string, any>>;
    sink_notes: Array<Record<string, any>>;
    recommended_actions: Array<Record<string, any>>;
    notes: string[];
  };
};
