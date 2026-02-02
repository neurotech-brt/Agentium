import { useEffect } from 'react';
import { useBackendStore } from '@/store/backendStore';
import { Wifi, WifiOff, Loader2 } from 'lucide-react';

interface ConnectionStatusProps {
    compact?: boolean; // New prop for compact mode (just circle)
}

export function ConnectionStatus({ compact = false }: ConnectionStatusProps) {
    const { status, startPolling, stopPolling } = useBackendStore();

    useEffect(() => {
        startPolling();
        return () => stopPolling();
    }, [startPolling, stopPolling]);

    const getStatusColor = () => {
        switch (status.status) {
            case 'connected':
                return 'bg-green-500';
            case 'connecting':
                return 'bg-yellow-500';
            case 'disconnected':
                return 'bg-red-500';
        }
    };

    const getStatusIcon = () => {
        switch (status.status) {
            case 'connected':
                return <Wifi className="w-4 h-4" />;
            case 'connecting':
                return <Loader2 className="w-4 h-4 animate-spin" />;
            case 'disconnected':
                return <WifiOff className="w-4 h-4" />;
        }
    };

    // Compact mode - just a circle
    if (compact) {
        return (
            <div className="relative group">
                <div className={`w-3 h-3 rounded-full ${getStatusColor()} ${status.status === 'connecting' ? 'animate-pulse' : ''}`} />
                <div className="absolute right-0 top-full mt-2 px-2 py-1 bg-gray-900 text-white text-xs rounded whitespace-nowrap opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all duration-200 z-50">
                    {status.status === 'connected' && status.latency ? `Connected (${status.latency}ms)` : status.status}
                </div>
            </div>
        );
    }

    // Full mode - original design
    return (
        <div className="flex items-center gap-2 px-3 py-1.5 rounded-full bg-gray-100 dark:bg-gray-800 text-sm">
            <div className={`w-2 h-2 rounded-full ${getStatusColor()}`} />
            {getStatusIcon()}
            <span className="capitalize hidden sm:inline">{status.status}</span>
            {status.latency && (
                <span className="text-xs text-gray-500 hidden md:inline">
                    ({status.latency}ms)
                </span>
            )}
        </div>
    );
}