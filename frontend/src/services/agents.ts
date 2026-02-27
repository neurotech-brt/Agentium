import { api } from './api';
import { Agent } from '../types';

export interface SpawnAgentRequest {
    child_type: 'council_member' | 'lead_agent' | 'task_agent';
    name: string;
}

export const agentsService = {
    getAgents: async (filters?: { type?: string; status?: string }): Promise<Agent[]> => {
        const params = new URLSearchParams();
        if (filters?.type) params.append('agent_type', filters.type);
        if (filters?.status) params.append('status', filters.status);

        const response = await api.get<{ agents: Agent[] }>(`/api/v1/agents?${params.toString()}`);
        return response.data.agents;
    },

    getAgent: async (id: string): Promise<Agent> => {
        const response = await api.get<Agent>(`/api/v1/agents/${id}`);
        return response.data;
    },

    spawnAgent: async (parentId: string, data: SpawnAgentRequest): Promise<Agent> => {
        const response = await api.post<{ agent: Agent }>(`/api/v1/agents/lifecycle/spawn?child_type=${data.child_type}&name=${encodeURIComponent(data.name)}`);
        return response.data.agent;
    },

    terminateAgent: async (id: string, reason: string): Promise<void> => {
        await api.post(`/api/v1/agents/lifecycle/${id}/terminate?reason=${encodeURIComponent(reason)}`);
    }
};
export interface ReassignAgentRequest {
    new_parent_id: string;
    reason?: string;
}

export interface CapabilityProfile {
    tier: string;
    agentium_id: string;
    base_capabilities: string[];
    granted_capabilities: string[];
    revoked_capabilities: string[];
    effective_capabilities: string[];
    total_count: number;
}

export const capabilitiesService = {
    getAgentCapabilities: async (agentiumId: string): Promise<CapabilityProfile> => {
        const response = await api.get<CapabilityProfile>(`/api/v1/capabilities/agent/${agentiumId}`);
        return response.data;
    },

    checkCapability: async (agentiumId: string, capability: string): Promise<boolean> => {
        const response = await api.post<{ has_capability: boolean }>('/api/v1/capabilities/check', {
            agentium_id: agentiumId,
            capability,
        });
        return response.data.has_capability;
    },

    validateReassignment: async (agentiumId: string, newParentId: string): Promise<{ valid: boolean; reason?: string }> => {
        // An agent can be reassigned if its type is compatible with the new parent's tier.
        // task_agent -> lead_agent (tier 2)
        // lead_agent -> council_member (tier 1) or head_of_council (tier 0)
        // We validate by checking spawn capability on new parent.
        const agentTier = agentiumId[0];
        const parentTier = newParentId[0];

        const capabilityNeeded =
            agentTier === '3' ? 'spawn_task_agent' :
            agentTier === '2' ? 'spawn_lead' :
            agentTier === '1' ? 'spawn_lead' : null;

        if (!capabilityNeeded) return { valid: false, reason: 'Head of Council cannot be reassigned.' };
        if (parentTier >= agentTier) return { valid: false, reason: 'New parent must outrank the agent.' };

        const hasCapability = await capabilitiesService.checkCapability(newParentId, capabilityNeeded);
        return hasCapability
            ? { valid: true }
            : { valid: false, reason: `New parent lacks '${capabilityNeeded}' capability.` };
    },
};

// Add reassign to agentsService
Object.assign(agentsService, {
    reassignAgent: async (agentId: string, data: ReassignAgentRequest): Promise<Agent> => {
        const response = await api.post<{ agent: Agent }>(
            `/api/v1/agents/lifecycle/${agentId}/reassign`,
            data
        );
        return response.data.agent;
    },
});