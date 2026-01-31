import { api } from './api';
import { ModelConfig } from '../types';
export type { ModelConfig };

export interface ProviderInfo {
    id: string;
    name: string;
    requires_api_key: boolean;
    supports_local: boolean;
    default_models: string[];
}

export interface ModelConfigCreate {
    provider: string;
    config_name: string;
    api_key?: string;
    api_base_url?: string;
    default_model: string;
    available_models?: string[];
    local_server_url?: string;
    is_default?: boolean;
    max_tokens?: number;
    temperature?: number;
    timeout_seconds?: number;
}

export interface ModelConfigUpdate {
    config_name?: string;
    api_key?: string;
    default_model?: string;
    available_models?: string[];
    is_default?: boolean;
    max_tokens?: number;
    temperature?: number;
    status?: string;
}

export interface TestResult {
    success: boolean;
    message: string;
    latency_ms?: number;
    model?: string;
    error?: string;
}

export interface UsageStats {
    period_days: number;
    total_tokens: number;
    total_requests: number;
    total_cost_usd: number;
    success_rate: number;
    daily_breakdown: Record<string, {
        tokens: number;
        requests: number;
        cost: number;
    }>;
}

export const modelsService = {
    getProviders: async (): Promise<ProviderInfo[]> => {
        const response = await api.get<ProviderInfo[]>('/models/providers');
        return response.data;
    },

    getConfigs: async (): Promise<ModelConfig[]> => {
        const response = await api.get<ModelConfig[]>('/models/configs');
        return response.data;
    },

    getConfig: async (id: string): Promise<ModelConfig> => {
        const response = await api.get<ModelConfig>(`/models/configs/${id}`);
        return response.data;
    },

    createConfig: async (config: ModelConfigCreate): Promise<ModelConfig> => {
        const response = await api.post<ModelConfig>('/models/configs', config);
        return response.data;
    },

    updateConfig: async (id: string, updates: ModelConfigUpdate): Promise<ModelConfig> => {
        const response = await api.put<ModelConfig>(`/models/configs/${id}`, updates);
        return response.data;
    },

    deleteConfig: async (id: string): Promise<void> => {
        await api.delete(`/models/configs/${id}`);
    },

    testConfig: async (id: string): Promise<TestResult> => {
        const response = await api.post<TestResult>(`/models/configs/${id}/test`);
        return response.data;
    },

    getUsage: async (id: string, days: number = 7): Promise<UsageStats> => {
        const response = await api.get<UsageStats>(`/models/configs/${id}/usage?days=${days}`);
        return response.data;
    },

    setDefault: async (id: string): Promise<void> => {
        await api.post(`/models/configs/${id}/set-default`);
    }
};
