import { useEffect, useRef, useState, useCallback } from 'react';
import { useAuthStore } from '@/store/authStore';

interface WebSocketMessage {
    type: 'message' | 'status' | 'error' | 'system';
    role?: 'sovereign' | 'head_of_council' | 'system';
    content: string;
    metadata?: any;
    timestamp?: string;
}

export function useWebSocketChat(onMessage: (msg: WebSocketMessage) => void) {
    const [isConnected, setIsConnected] = useState(false);
    const [isConnecting, setIsConnecting] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const ws = useRef<WebSocket | null>(null);
    const { user } = useAuthStore();

    const connect = useCallback(() => {
        if (ws.current?.readyState === WebSocket.OPEN) return;

        setIsConnecting(true);
        setError(null);

        // Get token from localStorage
        const token = localStorage.getItem('access_token');
        if (!token) {
            setError('Not authenticated');
            setIsConnecting(false);
            return;
        }

        // Connect with token in query param
        const WS_URL = import.meta.env.VITE_WS_URL || 'ws://localhost:8000';
        const wsUrl = `${WS_URL}/ws/chat?token=${encodeURIComponent(token)}`;

        ws.current = new WebSocket(wsUrl);

        ws.current.onopen = () => {
            console.log('WebSocket authenticated and connected');
            setIsConnected(true);
            setIsConnecting(false);
            setError(null);
        };

        ws.current.onmessage = (event) => {
            try {
                const data = JSON.parse(event.data);
                onMessage(data);
            } catch (e) {
                console.error('Failed to parse WebSocket message:', e);
            }
        };

        ws.current.onerror = (error) => {
            console.error('WebSocket error:', error);
            setError('Connection error');
            setIsConnected(false);
        };

        ws.current.onclose = (event) => {
            console.log('WebSocket closed:', event.code, event.reason);
            setIsConnected(false);
            setIsConnecting(false);

            // If closed due to auth error (4001), don't retry
            if (event.code === 4001) {
                setError('Authentication failed. Please login again.');
            } else {
                setError('Disconnected');
            }
        };
    }, [onMessage]);

    const disconnect = useCallback(() => {
        if (ws.current) {
            ws.current.close();
            ws.current = null;
        }
    }, []);

    const sendMessage = useCallback((content: string) => {
        if (ws.current?.readyState === WebSocket.OPEN) {
            ws.current.send(JSON.stringify({ content }));
            return true;
        }
        return false;
    }, []);

    // Auto-connect when user is authenticated
    useEffect(() => {
        if (user?.isAuthenticated && !isConnected && !isConnecting) {
            connect();
        }

        return () => {
            disconnect();
        };
    }, [user?.isAuthenticated, connect, disconnect]);

    // Reconnect on token change
    useEffect(() => {
        const handleStorage = (e: StorageEvent) => {
            if (e.key === 'access_token') {
                if (e.newValue) {
                    // Token added/changed, reconnect
                    disconnect();
                    setTimeout(connect, 100);
                } else {
                    // Token removed, disconnect
                    disconnect();
                }
            }
        };

        window.addEventListener('storage', handleStorage);
        return () => window.removeEventListener('storage', handleStorage);
    }, [connect, disconnect]);

    return {
        isConnected,
        isConnecting,
        error,
        connect,
        disconnect,
        sendMessage
    };
}