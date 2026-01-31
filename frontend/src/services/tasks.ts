import { api } from './api';
import { Task } from '../types';

export interface CreateTaskRequest {
    title: string;
    description: string;
    priority: 'low' | 'normal' | 'urgent' | 'critical';
    task_type: 'execution' | 'research';
}

export const tasksService = {
    getTasks: async (filters?: { status?: string; agent_id?: string }): Promise<Task[]> => {
        const params = new URLSearchParams();
        if (filters?.status) params.append('status', filters.status);
        if (filters?.agent_id) params.append('agent_id', filters.agent_id);

        const response = await api.get<{ tasks: Task[] }>(`/tasks?${params.toString()}`);
        return response.data.tasks;
    },

    createTask: async (data: CreateTaskRequest): Promise<Task> => {
        const params = new URLSearchParams();
        params.append('title', data.title);
        params.append('description', data.description);
        params.append('priority', data.priority);
        params.append('task_type', data.task_type);

        const response = await api.post<{ task: Task }>(`/tasks?${params.toString()}`);
        return response.data.task;
    },

    executeTask: async (taskId: string, agentId: string): Promise<any> => {
        const response = await api.post(`/tasks/${taskId}/execute?agent_id=${agentId}`);
        return response.data;
    }
};
