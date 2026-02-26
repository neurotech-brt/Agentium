// frontend/src/services/abTesting.ts
// API service layer for A/B Model Testing

import { api } from './api';

export interface ExperimentSummary {
  id: string;
  name: string;
  description: string;
  status: 'draft' | 'pending' | 'running' | 'completed' | 'failed' | 'cancelled';
  models_tested: number;
  progress: number;
  created_at: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ExperimentRun {
  id: string;
  model: string;
  config_id: string;
  iteration: number;
  status: 'pending' | 'running' | 'completed' | 'failed';
  tokens: number | null;
  latency_ms: number | null;
  cost_usd: number | null;
  quality_score: number | null;
  critic_plan_score: number | null;
  critic_code_score: number | null;
  critic_output_score: number | null;
  constitutional_violations: number;
  output_preview: string | null;
  error_message: string | null;
  started_at: string | null;
  completed_at: string | null;
}

export interface ModelComparison {
  config_id: string;
  model_name: string;
  avg_tokens: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  avg_quality_score: number;
  success_rate: number;
  total_runs: number;
}

export interface ExperimentDetail extends ExperimentSummary {
  task_template: string;
  system_prompt: string | null;
  test_iterations: number;
  runs: ExperimentRun[];
  comparison: {
    winner: {
      config_id: string;
      model: string;
      reason: string;
      confidence: number;
    };
    model_comparisons: { models: ModelComparison[] };
    created_at: string | null;
  } | null;
}

export interface CreateExperimentPayload {
  name: string;
  task_template: string;
  config_ids: string[];
  description?: string;
  system_prompt?: string;
  iterations?: number;
}

export interface Recommendation {
  task_category: string;
  recommended_model: string;
  avg_quality_score: number;
  avg_cost_usd: number;
  avg_latency_ms: number;
  success_rate: number;
  sample_size: number;
  last_updated: string | null;
}

export interface ABTestingStats {
  total_experiments: number;
  completed_experiments: number;
  running_experiments: number;
  total_model_runs: number;
  cached_recommendations: number;
}

const BASE = '/api/v1/ab-testing';

// FIX: All methods now extract .data from Axios response
export const abTestingApi = {
  createExperiment: (data: CreateExperimentPayload): Promise<ExperimentSummary> =>
    api.post(`${BASE}/experiments`, data).then(r => r.data),

  listExperiments: (status?: string): Promise<ExperimentSummary[]> =>
    api.get(`${BASE}/experiments${status ? `?status=${status}` : ''}`).then(r => r.data),

  getExperiment: (id: string): Promise<ExperimentDetail> =>
    api.get(`${BASE}/experiments/${id}`).then(r => r.data),

  cancelExperiment: (id: string): Promise<{ message: string }> =>
    api.post(`${BASE}/experiments/${id}/cancel`, {}).then(r => r.data),

  deleteExperiment: (id: string): Promise<{ message: string }> =>
    api.delete(`${BASE}/experiments/${id}`).then(r => r.data),

  getRecommendations: (taskCategory?: string): Promise<{ recommendations: Recommendation[]; total_categories: number }> =>
    api.get(`${BASE}/recommendations${taskCategory ? `?task_category=${taskCategory}` : ''}`).then(r => r.data),

  quickTest: (task: string, configIds: string[]): Promise<ExperimentDetail> =>
    api.post(`${BASE}/quick-test`, { task, config_ids: configIds }).then(r => r.data),

  getStats: (): Promise<ABTestingStats> =>
    api.get(`${BASE}/stats`).then(r => r.data),
};