// src/hooks/useSystemTab.ts
// Owns all data-fetching, WebSocket lifecycle, and container action logic
// for the System tab. Keeps SystemTab.tsx purely presentational.

import { useState, useEffect, useCallback, useRef } from 'react';
import { useBackendStore } from '@/store/backendStore';
import { hostAccessApi } from '@/services/hostAccessApi';

// ── Types (exported so SystemTab.tsx can import them) ─────────────────────────

export interface SystemStatus {
    cpu: { usage: number; cores: number; load: number[] };
    memory: { total: number; used: number; free: number; percentage: number };
    disk: { total: number; used: number; free: number; percentage: number };
    uptime: { seconds: number; formatted: string };
}

export interface Container {
    id: string;
    name: string;
    status: string;
    image: string;
    created: string;
}

export interface CommandLog {
    id: string;
    command: string;
    status: 'pending' | 'approved' | 'rejected' | 'executed';
    timestamp: Date;
    executor?: string;
}

// ── Hook ──────────────────────────────────────────────────────────────────────

export function useSystemTab() {
    const { status: backendStatus } = useBackendStore();

    const [systemStatus, setSystemStatus]   = useState<SystemStatus | null>(null);
    const [containers,   setContainers]     = useState<Container[]>([]);
    const [commandLogs,  setCommandLogs]    = useState<CommandLog[]>([]);
    const [isLoading,    setIsLoading]      = useState(false); // container action buttons
    const [error,        setError]          = useState<string | null>(null);

    // Stable refs so the reconnect closure never captures a stale function ref
    const wsRef            = useRef<{ send: (d: unknown) => void; close: () => void } | null>(null);
    const retryTimeoutRef  = useRef<ReturnType<typeof setTimeout> | null>(null);
    const retriesRef       = useRef(0);
    const mountedRef       = useRef(true);

    // ── Parallel data fetch ───────────────────────────────────────────────────
    // C11: replaced three sequential fetches with Promise.all — cuts initial
    //      load time to the duration of the slowest single request.

    const refresh = useCallback(async () => {
        try {
            const [status, ctrs, logs] = await Promise.all([
                hostAccessApi.getSystemStatus(),
                hostAccessApi.getContainers(),
                hostAccessApi.getCommandHistory(50),
            ]);
            if (!mountedRef.current) return;
            setSystemStatus(status);
            setContainers(ctrs);
            setCommandLogs(logs);
            setError(null);
        } catch {
            if (!mountedRef.current) return;
            setError('Failed to load system data. Check backend connectivity.');
        }
    }, []);

    // ── WebSocket with exponential-backoff reconnect ──────────────────────────
    // C2: onClose fires a retry with capped backoff instead of silently dying.

    const connectWebSocket = useCallback(() => {
        wsRef.current = hostAccessApi.connectWebSocket(
            (data: any) => {
                retriesRef.current = 0; // successful message resets backoff counter
                if (!mountedRef.current) return;

                if (data.type === 'system_status') {
                    setSystemStatus(data.payload);
                } else if (data.type === 'container_update') {
                    hostAccessApi.getContainers()
                        .then(ctrs => { if (mountedRef.current) setContainers(ctrs); })
                        .catch(() => {});
                } else if (data.type === 'command_log') {
                    setCommandLogs(prev => [data.payload, ...prev]);
                }
            },
            () => {
                // onClose — schedule reconnect with exponential backoff (max 30 s)
                if (!mountedRef.current) return;
                const delay = Math.min(1000 * 2 ** retriesRef.current, 30_000);
                retriesRef.current += 1;
                retryTimeoutRef.current = setTimeout(connectWebSocket, delay);
            },
        );
    }, []);

    // ── Container actions ─────────────────────────────────────────────────────

    const handleContainerAction = useCallback(async (
        containerId: string,
        action: 'start' | 'stop' | 'restart' | 'remove',
    ) => {
        setIsLoading(true);
        try {
            await hostAccessApi.manageContainer(containerId, action);
            const ctrs = await hostAccessApi.getContainers();
            if (mountedRef.current) setContainers(ctrs);
        } catch {
            if (mountedRef.current)
                setError(`Failed to ${action} container. Please try again.`);
        } finally {
            if (mountedRef.current) setIsLoading(false);
        }
    }, []);

    // ── Lifecycle ─────────────────────────────────────────────────────────────

    useEffect(() => {
        mountedRef.current = true;

        if (backendStatus.status !== 'connected') return;

        refresh();
        connectWebSocket();

        return () => {
            mountedRef.current = false;
            if (retryTimeoutRef.current) clearTimeout(retryTimeoutRef.current);
            wsRef.current?.close();
        };
    }, [backendStatus.status, refresh, connectWebSocket]);

    return {
        systemStatus,
        containers,
        commandLogs,
        isLoading,
        error,
        refresh,
        handleContainerAction,
        clearError: () => setError(null),
    };
}