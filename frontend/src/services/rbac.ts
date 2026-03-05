import { api } from './api';

export interface RBACUser {
    id: string;
    username: string;
    email?: string;
    is_active: boolean;
    is_admin: boolean;
    /** Computed by backend — e.g. "primary_sovereign" | "deputy_sovereign" | "observer" */
    effective_role: string;
    active_delegations?: Delegation[];
}

export interface Delegation {
    id: string;
    grantor_id: string;
    grantee_id: string;
    capabilities: string[];
    is_active: boolean;
    is_emergency: boolean;
    expires_at?: string;
    reason?: string;
}

export const rbacService = {
    async listUsersWithRoles(): Promise<RBACUser[]> {
        const response = await api.get('/api/v1/rbac/roles');
        return response.data;
    },

    async delegateCapability(
        granteeId: string,
        capabilities: string[],
        reason?: string,
        expiresAt?: string,
    ): Promise<Delegation> {
        const response = await api.post('/api/v1/rbac/delegate', {
            grantee_id: granteeId,
            capabilities,
            reason,
            expires_at: expiresAt,
        });
        return response.data;
    },

    async revokeDelegation(delegationId: string): Promise<Delegation> {
        const response = await api.delete(`/api/v1/rbac/delegate/${delegationId}`);
        return response.data;
    },

    async emergencyTransfer(
        newSovereignId: string,
        reason: string,
    ): Promise<{ success: boolean; message: string; delegation_record: Delegation }> {
        const response = await api.post('/api/v1/rbac/emergency-transfer', {
            new_sovereign_id: newSovereignId,
            reason,
        });
        return response.data;
    },

    async getMyPermissions(): Promise<{
        user_id: string;
        role: string;
        effective_permissions: string[];
    }> {
        const response = await api.get('/api/v1/rbac/permissions/me');
        return response.data;
    },
};