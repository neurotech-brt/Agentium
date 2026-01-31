import { api } from './api';
import { Constitution } from '../types';

export const constitutionService = {
    getCurrentConstitution: async (): Promise<Constitution> => {
        const response = await api.get<Constitution>('/constitution/current');
        return response.data;
    },

    updateConstitution: async (data: {
        preamble: string;
        articles: string | Record<string, string>;
        prohibited_actions: string[];
        sovereign_preferences: Record<string, any>;
    }): Promise<Constitution> => {
        // Ensure articles is stringified if it's an object, as backend expects string or handles it?
        // Backend `main.py` handles both: `json.loads(data.articles) if isinstance(data.articles, str) else data.articles`
        // But `ConstitutionUpdate` model defines `articles: str`. So we should stringify.

        const payload = {
            ...data,
            articles: typeof data.articles === 'string' ? data.articles : JSON.stringify(data.articles)
        };

        const response = await api.post<Constitution>('/constitution/update', payload);
        return response.data;
    }
};
