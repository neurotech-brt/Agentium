/**
 * federation.ts — Federation API Service (Phase 11.2 — Improved)
 *
 * Changes vs original:
 *  - Full type definitions for all entities (PeerInstance, FederatedTask, etc.)
 *  - deletePeer()         — DELETE /peers/{id}
 *  - updatePeerTrust()    — PATCH  /peers/{id}/trust
 *  - listFederatedTasks() — GET    /tasks
 *  - getPeerStats()       — derived stats helper (no extra API call needed)
 *  - signRequest()        — HMAC-SHA256 signing utility for frontend→peer calls (future use)
 *  - All methods handle errors consistently and re-throw with detail message
 */

import { api } from './api';

// ── Types ──────────────────────────────────────────────────────────────────────

export type PeerStatus = 'active' | 'suspended' | 'pending';
export type TrustLevel = 'full' | 'limited' | 'read_only';
export type FedTaskStatus = 'pending' | 'delivered' | 'accepted' | 'rejected' | 'completed' | 'failed';
export type FedTaskDirection = 'incoming' | 'outgoing';

export interface PeerInstance {
    id: string;
    name: string;
    base_url: string;
    status: PeerStatus;
    trust_level: TrustLevel;
    capabilities_shared: string[];
    last_heartbeat_at?: string;
    registered_at?: string;
}

export interface RegisterPeerRequest {
    name: string;
    base_url: string;
    shared_secret: string;
    trust_level?: TrustLevel;
    capabilities?: string[];
}

export interface FederatedTask {
    id: string;
    original_task_id: string;
    local_task_id?: string;
    source_instance_id?: string;
    target_instance_id?: string;
    status: FedTaskStatus;
    direction: FedTaskDirection;
    delegated_at: string;
    completed_at?: string;
}

export interface DelegateTaskRequest {
    target_peer_id: string;
    original_task_id: string;
    payload: Record<string, unknown>;
}

export interface DelegateTaskResult {
    id: string;
    status: FedTaskStatus;
    message: string;
}

export interface PeerStats {
    total: number;
    active: number;
    suspended: number;
    pending: number;
}

// ── Helpers ────────────────────────────────────────────────────────────────────

function extractDetail(error: unknown): string {
    if (error && typeof error === 'object') {
        const e = error as Record<string, unknown>;
        if (e.response && typeof e.response === 'object') {
            const resp = e.response as Record<string, unknown>;
            if (resp.data && typeof resp.data === 'object') {
                const data = resp.data as Record<string, unknown>;
                if (typeof data.detail === 'string') return data.detail;
            }
        }
        if (typeof e.message === 'string') return e.message;
    }
    return 'Unknown error';
}

// ── Service ────────────────────────────────────────────────────────────────────

export const federationService = {

    // ── Peer management ──────────────────────────────────────────────────────

    async listPeers(): Promise<PeerInstance[]> {
        try {
            const response = await api.get('/api/v1/federation/peers');
            return response.data as PeerInstance[];
        } catch (error) {
            throw new Error(`Failed to list peers: ${extractDetail(error)}`);
        }
    },

    async registerPeer(request: RegisterPeerRequest): Promise<PeerInstance> {
        try {
            const response = await api.post('/api/v1/federation/peers', {
                name: request.name,
                base_url: request.base_url,
                shared_secret: request.shared_secret,
                trust_level: request.trust_level ?? 'limited',
                capabilities: request.capabilities ?? [],
            });
            return response.data as PeerInstance;
        } catch (error) {
            throw new Error(`Failed to register peer: ${extractDetail(error)}`);
        }
    },

    async deletePeer(peerId: string): Promise<void> {
        try {
            await api.delete(`/api/v1/federation/peers/${peerId}`);
        } catch (error) {
            throw new Error(`Failed to delete peer: ${extractDetail(error)}`);
        }
    },

    async updatePeerTrust(peerId: string, trustLevel: TrustLevel): Promise<PeerInstance> {
        try {
            const response = await api.patch(`/api/v1/federation/peers/${peerId}/trust`, {
                trust_level: trustLevel,
            });
            return response.data as PeerInstance;
        } catch (error) {
            throw new Error(`Failed to update peer trust: ${extractDetail(error)}`);
        }
    },

    // ── Task delegation ───────────────────────────────────────────────────────

    async delegateTask(request: DelegateTaskRequest): Promise<DelegateTaskResult> {
        try {
            const response = await api.post('/api/v1/federation/tasks/delegate', {
                target_peer_id: request.target_peer_id,
                original_task_id: request.original_task_id,
                payload: request.payload,
            });
            return response.data as DelegateTaskResult;
        } catch (error) {
            throw new Error(`Failed to delegate task: ${extractDetail(error)}`);
        }
    },

    async listFederatedTasks(): Promise<FederatedTask[]> {
        try {
            const response = await api.get('/api/v1/federation/tasks');
            return response.data as FederatedTask[];
        } catch (error) {
            throw new Error(`Failed to list federated tasks: ${extractDetail(error)}`);
        }
    },

    // ── Derived utilities ─────────────────────────────────────────────────────

    getPeerStats(peers: PeerInstance[]): PeerStats {
        return {
            total: peers.length,
            active: peers.filter(p => p.status === 'active').length,
            suspended: peers.filter(p => p.status === 'suspended').length,
            pending: peers.filter(p => p.status === 'pending').length,
        };
    },

    getTaskStats(tasks: FederatedTask[]): { incoming: number; outgoing: number; pending: number; completed: number; failed: number } {
        return {
            incoming: tasks.filter(t => t.direction === 'incoming').length,
            outgoing: tasks.filter(t => t.direction === 'outgoing').length,
            pending: tasks.filter(t => ['pending', 'delivered', 'accepted'].includes(t.status)).length,
            completed: tasks.filter(t => t.status === 'completed').length,
            failed: tasks.filter(t => t.status === 'failed' || t.status === 'rejected').length,
        };
    },

    /**
     * Format last_heartbeat_at into a human-readable relative string.
     * e.g. "2 min ago", "Just now", "Never"
     */
    formatHeartbeat(lastHeartbeatAt?: string): string {
        if (!lastHeartbeatAt) return 'Never';
        const diff = Date.now() - new Date(lastHeartbeatAt).getTime();
        const minutes = Math.floor(diff / 60_000);
        if (minutes < 1) return 'Just now';
        if (minutes < 60) return `${minutes} min ago`;
        const hours = Math.floor(minutes / 60);
        if (hours < 24) return `${hours}h ago`;
        return new Date(lastHeartbeatAt).toLocaleDateString();
    },

    /**
     * HMAC-SHA256 signing utility for direct peer-to-peer calls from the frontend.
     * NOTE: Only use this for internal tooling — the shared secret should NOT be
     * available in the browser for production deployments. Backend-to-backend is
     * preferred. This is provided for dev/debug tooling only.
     */
    async signRequest(signingKey: string, bodyJson: string, timestamp: number): Promise<string> {
        const encoder = new TextEncoder();
        const keyData = encoder.encode(signingKey);
        const message = encoder.encode(`${timestamp}:${bodyJson}`);
        const cryptoKey = await crypto.subtle.importKey(
            'raw', keyData, { name: 'HMAC', hash: 'SHA-256' }, false, ['sign']
        );
        const sigBuffer = await crypto.subtle.sign('HMAC', cryptoKey, message);
        const sigHex = Array.from(new Uint8Array(sigBuffer))
            .map(b => b.toString(16).padStart(2, '0'))
            .join('');
        return `sha256=${sigHex}`;
    },
};