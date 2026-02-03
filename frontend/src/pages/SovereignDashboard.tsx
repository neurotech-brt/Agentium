import { useEffect, useState } from 'react';
import { useAuthStore } from '@/store/authStore';
import { useBackendStore } from '@/store/backendStore';
import {
    Shield,
    Server,
    Activity,
    AlertTriangle,
    Terminal,
    Play,
    Square,
    RotateCw,
    Trash2,
    CheckCircle,
    XCircle,
    Clock
} from 'lucide-react';
import { hostAccessApi } from '@/services/hostAccessApi';

interface SystemStatus {
    cpu: number;
    memory: number;
    disk: number;
    uptime: number;
}

interface Container {
    id: string;
    name: string;
    status: string;
    image: string;
    created: string;
}

interface CommandLog {
    id: string;
    command: string;
    status: 'pending' | 'approved' | 'rejected' | 'executed';
    timestamp: Date;
    executor?: string;
}

export function SovereignDashboard() {
    const { user } = useAuthStore();
    const { status: backendStatus } = useBackendStore();
    const [systemStatus, setSystemStatus] = useState<SystemStatus | null>(null);
    const [containers, setContainers] = useState<Container[]>([]);
    const [commandLogs, setCommandLogs] = useState<CommandLog[]>([]);
    const [selectedContainer, setSelectedContainer] = useState<string | null>(null);
    const [isLoading, setIsLoading] = useState(false);

    useEffect(() => {
        if (backendStatus.status === 'connected') {
            fetchSystemStatus();
            fetchContainers();
            fetchCommandLogs();

            // Set up WebSocket for real-time updates
            const ws = hostAccessApi.connectWebSocket((data) => {
                if (data.type === 'system_status') {
                    setSystemStatus(data.payload);
                } else if (data.type === 'container_update') {
                    fetchContainers();
                } else if (data.type === 'command_log') {
                    setCommandLogs(prev => [data.payload, ...prev]);
                }
            });

            return () => {
                ws.close();
            };
        }
    }, [backendStatus.status]);

    const fetchSystemStatus = async () => {
        try {
            const data = await hostAccessApi.getSystemStatus();
            setSystemStatus(data);
        } catch (error) {
            console.error('Failed to fetch system status:', error);
        }
    };

    const fetchContainers = async () => {
        try {
            const data = await hostAccessApi.getContainers();
            setContainers(data);
        } catch (error) {
            console.error('Failed to fetch containers:', error);
        }
    };

    const fetchCommandLogs = async () => {
        try {
            const data = await hostAccessApi.getCommandHistory(50);
            setCommandLogs(data);
        } catch (error) {
            console.error('Failed to fetch command logs:', error);
        }
    };

    const handleContainerAction = async (containerId: string, action: 'start' | 'stop' | 'restart' | 'remove') => {
        setIsLoading(true);
        try {
            await hostAccessApi.manageContainer(containerId, action);
            await fetchContainers();
        } catch (error) {
            console.error(`Failed to ${action} container:`, error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleExecuteCommand = async (command: string, params: Record<string, any> = {}) => {
        try {
            await hostAccessApi.executeSovereignCommand(command, params);
            await fetchCommandLogs();
        } catch (error) {
            console.error('Failed to execute command:', error);
        }
    };

    const getStatusColor = (status: string) => {
        switch (status.toLowerCase()) {
            case 'running':
                return 'text-green-600 bg-green-100 dark:bg-green-900/30 dark:text-green-400';
            case 'stopped':
            case 'exited':
                return 'text-red-600 bg-red-100 dark:bg-red-900/30 dark:text-red-400';
            case 'paused':
                return 'text-yellow-600 bg-yellow-100 dark:bg-yellow-900/30 dark:text-yellow-400';
            default:
                return 'text-gray-600 bg-gray-100 dark:bg-gray-900/30 dark:text-gray-400';
        }
    };

    const getCommandStatusIcon = (status: string) => {
        switch (status) {
            case 'approved':
            case 'executed':
                return <CheckCircle className="w-4 h-4 text-green-600" />;
            case 'rejected':
                return <XCircle className="w-4 h-4 text-red-600" />;
            case 'pending':
                return <Clock className="w-4 h-4 text-yellow-600" />;
            default:
                return null;
        }
    };

    if (!user?.isSovereign) {
        return (
            <div className="flex items-center justify-center h-full">
                <div className="text-center">
                    <Shield className="w-16 h-16 text-red-600 mx-auto mb-4" />
                    <h2 className="text-2xl font-bold text-gray-900 dark:text-white mb-2">
                        Access Denied
                    </h2>
                    <p className="text-gray-600 dark:text-gray-400">
                        Only Sovereign users can access this dashboard.
                    </p>
                </div>
            </div>
        );
    }

    return (
        <div className="space-y-6">
            {/* Header */}
            <div className="flex items-center justify-between">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Sovereign Control Panel
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Full system access and administrative controls
                    </p>
                </div>
                <div className="flex items-center gap-2">
                    <Shield className="w-8 h-8 text-blue-600" />
                </div>
            </div>

            {/* System Status Grid */}
            {systemStatus && (
                <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">CPU Usage</span>
                            <Activity className="w-4 h-4 text-blue-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {systemStatus.cpu.toFixed(1)}%
                        </div>
                        <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                className="bg-blue-600 h-2 rounded-full transition-all"
                                style={{ width: `${systemStatus.cpu}%` }}
                            />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Memory</span>
                            <Server className="w-4 h-4 text-purple-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {systemStatus.memory.toFixed(1)}%
                        </div>
                        <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                className="bg-purple-600 h-2 rounded-full transition-all"
                                style={{ width: `${systemStatus.memory}%` }}
                            />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Disk</span>
                            <Server className="w-4 h-4 text-green-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {systemStatus.disk.toFixed(1)}%
                        </div>
                        <div className="mt-2 w-full bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                            <div
                                className="bg-green-600 h-2 rounded-full transition-all"
                                style={{ width: `${systemStatus.disk}%` }}
                            />
                        </div>
                    </div>

                    <div className="bg-white dark:bg-gray-800 p-6 rounded-xl border border-gray-200 dark:border-gray-700">
                        <div className="flex items-center justify-between mb-2">
                            <span className="text-sm text-gray-600 dark:text-gray-400">Uptime</span>
                            <Clock className="w-4 h-4 text-orange-600" />
                        </div>
                        <div className="text-2xl font-bold text-gray-900 dark:text-white">
                            {Math.floor(systemStatus.uptime / 3600)}h
                        </div>
                        <div className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {Math.floor((systemStatus.uptime % 3600) / 60)}m running
                        </div>
                    </div>
                </div>
            )}

            {/* Container Management */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center justify-between">
                        <div className="flex items-center gap-3">
                            <Terminal className="w-5 h-5 text-blue-600" />
                            <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                                Container Management
                            </h2>
                        </div>
                        <button
                            onClick={fetchContainers}
                            className="px-3 py-1.5 text-sm bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                        >
                            Refresh
                        </button>
                    </div>
                </div>

                <div className="overflow-x-auto">
                    <table className="w-full">
                        <thead className="bg-gray-50 dark:bg-gray-900/50">
                            <tr>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Name
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Status
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Image
                                </th>
                                <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Created
                                </th>
                                <th className="px-6 py-3 text-right text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider">
                                    Actions
                                </th>
                            </tr>
                        </thead>
                        <tbody className="divide-y divide-gray-200 dark:divide-gray-700">
                            {containers.map((container) => (
                                <tr key={container.id} className="hover:bg-gray-50 dark:hover:bg-gray-700/50">
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <div className="text-sm font-medium text-gray-900 dark:text-white">
                                            {container.name}
                                        </div>
                                        <div className="text-xs text-gray-500 dark:text-gray-400">
                                            {container.id.substring(0, 12)}
                                        </div>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap">
                                        <span className={`px-2 py-1 text-xs font-medium rounded-full ${getStatusColor(container.status)}`}>
                                            {container.status}
                                        </span>
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                                        {container.image}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-600 dark:text-gray-400">
                                        {new Date(container.created).toLocaleDateString()}
                                    </td>
                                    <td className="px-6 py-4 whitespace-nowrap text-right text-sm">
                                        <div className="flex items-center justify-end gap-2">
                                            <button
                                                onClick={() => handleContainerAction(container.id, 'start')}
                                                disabled={isLoading || container.status === 'running'}
                                                className="p-1.5 text-green-600 hover:bg-green-50 dark:hover:bg-green-900/30 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                                title="Start"
                                            >
                                                <Play className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleContainerAction(container.id, 'stop')}
                                                disabled={isLoading || container.status !== 'running'}
                                                className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                                title="Stop"
                                            >
                                                <Square className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleContainerAction(container.id, 'restart')}
                                                disabled={isLoading}
                                                className="p-1.5 text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/30 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                                title="Restart"
                                            >
                                                <RotateCw className="w-4 h-4" />
                                            </button>
                                            <button
                                                onClick={() => handleContainerAction(container.id, 'remove')}
                                                disabled={isLoading}
                                                className="p-1.5 text-red-600 hover:bg-red-50 dark:hover:bg-red-900/30 rounded disabled:opacity-50 disabled:cursor-not-allowed"
                                                title="Remove"
                                            >
                                                <Trash2 className="w-4 h-4" />
                                            </button>
                                        </div>
                                    </td>
                                </tr>
                            ))}
                        </tbody>
                    </table>
                    {containers.length === 0 && (
                        <div className="text-center py-12">
                            <Terminal className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-500 dark:text-gray-400">No containers found</p>
                        </div>
                    )}
                </div>
            </div>

            {/* Command History */}
            <div className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700">
                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                    <div className="flex items-center gap-3">
                        <AlertTriangle className="w-5 h-5 text-yellow-600" />
                        <h2 className="text-lg font-semibold text-gray-900 dark:text-white">
                            Command History
                        </h2>
                    </div>
                </div>

                <div className="divide-y divide-gray-200 dark:divide-gray-700">
                    {commandLogs.slice(0, 10).map((log) => (
                        <div key={log.id} className="p-4 hover:bg-gray-50 dark:hover:bg-gray-700/50">
                            <div className="flex items-center justify-between">
                                <div className="flex-1">
                                    <div className="flex items-center gap-2 mb-1">
                                        {getCommandStatusIcon(log.status)}
                                        <code className="text-sm font-mono text-gray-900 dark:text-white">
                                            {log.command}
                                        </code>
                                    </div>
                                    <div className="flex items-center gap-4 text-xs text-gray-500 dark:text-gray-400">
                                        <span>{new Date(log.timestamp).toLocaleString()}</span>
                                        {log.executor && <span>Executor: {log.executor}</span>}
                                    </div>
                                </div>
                            </div>
                        </div>
                    ))}
                    {commandLogs.length === 0 && (
                        <div className="text-center py-12">
                            <CheckCircle className="w-12 h-12 text-gray-400 mx-auto mb-3" />
                            <p className="text-gray-500 dark:text-gray-400">No command history</p>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}