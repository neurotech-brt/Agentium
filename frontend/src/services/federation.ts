import { api } from './api';

export interface PeerInstance {
    id: string;
    name: string;
    base_url: string;
    status: string;
    trust_level: string;
    last_heartbeat_at?: string;
}

export interface DelegatedTaskResult {
    id: string;
    status: string;
}

export const federationService = {
    async listPeers(): Promise<PeerInstance[]> {
        const response = await api.get('/api/v1/federation/peers');
        return response.data;
    },

    async registerPeer(
        name: string,
        baseUrl: string,
        sharedSecret: string,
        trustLevel = 'limited',
        capabilities: string[] = [],
    ): Promise<PeerInstance> {
        const response = await api.post('/api/v1/federation/peers', {
            name,
            base_url: baseUrl,
            shared_secret: sharedSecret,
            trust_level: trustLevel,
            capabilities,
        });
        return response.data;
    },

    async delegateTask(
        targetPeerId: string,
        originalTaskId: string,
        payload: Record<string, unknown>,
    ): Promise<DelegatedTaskResult> {
        const response = await api.post('/api/v1/federation/tasks/delegate', {
            target_peer_id: targetPeerId,
            original_task_id: originalTaskId,
            payload,
        });
        return response.data;
    },
};