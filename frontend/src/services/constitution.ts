import { api } from './api';
import { Constitution, ConstitutionArticle } from '../types';

export const constitutionService = {
    getCurrentConstitution: async (): Promise<Constitution> => {
        const response = await api.get<Constitution>('/api/v1/constitution');
        return response.data;
    },

    updateConstitution: async (data: {
        preamble: string;
        articles: Record<string, ConstitutionArticle>;
        prohibited_actions: string[];
        sovereign_preferences: Record<string, unknown>;
    }): Promise<Constitution> => {
        const payload = {
            preamble: data.preamble,
            articles: data.articles,
            prohibited_actions: Array.isArray(data.prohibited_actions) ? data.prohibited_actions : [],
            sovereign_preferences: data.sovereign_preferences ?? {},
        };

        const response = await api.post<Constitution>('/api/v1/constitution/update', payload);
        return response.data;
    },
};