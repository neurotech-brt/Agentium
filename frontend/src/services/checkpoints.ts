/**
 * Checkpoints Service - Frontend API for execution checkpoints.
 */

import { api } from './api';

// ============================================================================
// Types
// ============================================================================

export type CheckpointPhase = 'plan_approved' | 'execution_complete' | 'critique_passed' | 'manual';

export interface Checkpoint {
    id: string;
    agentium_id: string;
    session_id: string;
    task_id: string;
    phase: CheckpointPhase;
    branch_name: string;
    parent_checkpoint_id?: string;
    agent_states: Record<string, any>;
    artifacts: Record<string, any>;
    task_state_snapshot: Record<string, any>;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

export interface CreateCheckpointRequest {
    task_id: string;
    phase: CheckpointPhase;
    artifacts?: Record<string, any>;
}

export interface BranchRequest {
    branch_name: string;
}

// ============================================================================
// Checkpoints Service
// ============================================================================

export const checkpointsService = {
    /**
     * Get all checkpoints, optionally filtered by session_id or task_id.
     */
    getCheckpoints: async (filters?: { session_id?: string; task_id?: string }): Promise<Checkpoint[]> => {
        const params = new URLSearchParams();
        if (filters?.session_id) params.append('session_id', filters.session_id);
        if (filters?.task_id) params.append('task_id', filters.task_id);
        const query = params.toString() ? `?${params.toString()}` : '';

        const response = await api.get<Checkpoint[]>(`/api/v1/checkpoints${query}`);
        return response.data || [];
    },

    /**
     * Get a specific checkpoint by ID.
     */
    getCheckpoint: async (checkpointId: string): Promise<Checkpoint> => {
        const response = await api.get<Checkpoint>(`/api/v1/checkpoints/${checkpointId}`);
        return response.data;
    },

    /**
     * Create a new checkpoint.
     */
    createCheckpoint: async (data: CreateCheckpointRequest): Promise<Checkpoint> => {
        const response = await api.post<Checkpoint>('/api/v1/checkpoints', data);
        return response.data;
    },

    /**
     * Resume execution from a checkpoint (time-travel).
     */
    resumeFromCheckpoint: async (checkpointId: string): Promise<any> => {
        const response = await api.post(`/api/v1/checkpoints/${checkpointId}/resume`);
        return response.data;
    },

    /**
     * Create a new branch from a checkpoint.
     */
    branchFromCheckpoint: async (checkpointId: string, branchName: string): Promise<any> => {
        const response = await api.post(`/api/v1/checkpoints/${checkpointId}/branch`, {
            branch_name: branchName,
        });
        return response.data;
    },
};

// ============================================================================
// Utility Functions
// ============================================================================

/**
 * Get human-readable phase label.
 */
export function getPhaseLabel(phase: CheckpointPhase): string {
    switch (phase) {
        case 'plan_approved':
            return 'Plan Approved';
        case 'execution_complete':
            return 'Execution Complete';
        case 'critique_passed':
            return 'Critique Passed';
        case 'manual':
            return 'Manual Checkpoint';
        default:
            return phase;
    }
}

/**
 * Get color for phase.
 */
export function getPhaseColor(phase: CheckpointPhase): string {
    switch (phase) {
        case 'plan_approved':
            return '#3b82f6';
        case 'execution_complete':
            return '#f59e0b';
        case 'critique_passed':
            return '#10b981';
        case 'manual':
            return '#8b5cf6';
        default:
            return '#6b7280';
    }
}
