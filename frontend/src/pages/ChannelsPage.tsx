import { useState } from 'react';
import {
    MessageCircle,
    Slack,
    Mail,
    Smartphone,
    Plus,
    Power,
    Settings,
    QrCode,
    Copy,
    CheckCircle,
    AlertCircle,
    RefreshCw
} from 'lucide-react';
import toast from 'react-hot-toast';

interface ChannelConfig {
    id: string;
    type: 'whatsapp' | 'slack' | 'discord' | 'email' | 'telegram';
    name: string;
    status: 'connected' | 'disconnected' | 'error' | 'pending';
    webhookUrl?: string;
    connectedSince?: string;
    lastMessage?: string;
    assignedAgent?: string;
    config: {
        phoneNumber?: string;
        apiKey?: string;
        botToken?: string;
        emailAddress?: string;
        [key: string]: any;
    };
}

export function ChannelsPage() {
    const [channels, setChannels] = useState<ChannelConfig[]>([
        {
            id: '1',
            type: 'whatsapp',
            name: 'Production WhatsApp',
            status: 'connected',
            connectedSince: '2024-01-15',
            lastMessage: '2 mins ago',
            assignedAgent: '00001',
            config: { phoneNumber: '+1-555-0123' }
        }
    ]);

    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedType, setSelectedType] = useState<string | null>(null);
    const [qrCode, setQrCode] = useState<string | null>(null);

    const channelTypes = [
        {
            id: 'whatsapp',
            name: 'WhatsApp',
            icon: Smartphone,
            description: 'Connect via WhatsApp Business API',
            color: 'green',
            requiresQR: true
        },
        {
            id: 'slack',
            name: 'Slack',
            icon: Slack,
            description: 'Slack Bot integration',
            color: 'purple',
            requiresQR: false
        },
        {
            id: 'telegram',
            name: 'Telegram',
            icon: MessageCircle,
            description: 'Telegram Bot API',
            color: 'blue',
            requiresQR: false
        },
        {
            id: 'email',
            name: 'Email',
            icon: Mail,
            description: 'IMAP/SMTP Email integration',
            color: 'red',
            requiresQR: false
        }
    ];

    const handleConnect = async (type: string) => {
        setSelectedType(type);

        if (type === 'whatsapp') {
            // Simulate getting QR code from backend
            setQrCode('data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNk+M9QDwADhgGAWjR9awAAAABJRU5ErkJggg==');
            toast.success('Scan the QR code with WhatsApp');
        } else if (type === 'slack') {
            toast.success('Configure Slack Bot Token in settings');
        }
    };

    const handleCopyWebhook = (url: string) => {
        navigator.clipboard.writeText(url);
        toast.success('Webhook URL copied');
    };

    const getStatusColor = (status: string) => {
        const colors = {
            connected: 'bg-green-500',
            disconnected: 'bg-gray-400',
            error: 'bg-red-500',
            pending: 'bg-yellow-500'
        };
        return colors[status] || 'bg-gray-400';
    };

    return (
        <div className="max-w-6xl mx-auto">
            {/* Header */}
            <div className="flex items-center justify-between mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Communication Channels
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Manage multi-channel integrations (WhatsApp, Slack, Email, etc.)
                    </p>
                </div>

                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    Add Channel
                </button>
            </div>

            {/* Active Channels Grid */}
            <div className="grid grid-cols-1 md:grid-cols-2 gap-6 mb-8">
                {channels.map((channel) => {
                    const typeInfo = channelTypes.find(t => t.id === channel.type);
                    const Icon = typeInfo?.icon || MessageCircle;

                    return (
                        <div
                            key={channel.id}
                            className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 p-6 hover:shadow-lg transition-shadow"
                        >
                            <div className="flex items-start justify-between mb-4">
                                <div className="flex items-center gap-3">
                                    <div className={`w-12 h-12 rounded-lg bg-${typeInfo?.color}-100 dark:bg-${typeInfo?.color}-900/30 flex items-center justify-center`}>
                                        <Icon className={`w-6 h-6 text-${typeInfo?.color}-600`} />
                                    </div>
                                    <div>
                                        <h3 className="font-semibold text-gray-900 dark:text-white flex items-center gap-2">
                                            {channel.name}
                                            <span className={`w-2 h-2 rounded-full ${getStatusColor(channel.status)}`} />
                                        </h3>
                                        <p className="text-sm text-gray-500 dark:text-gray-400 capitalize">
                                            {channel.type} • {channel.status}
                                        </p>
                                    </div>
                                </div>

                                <button
                                    onClick={() => toast.success('Settings opened')}
                                    className="p-2 text-gray-400 hover:text-gray-600 dark:hover:text-gray-300"
                                >
                                    <Settings className="w-5 h-5" />
                                </button>
                            </div>

                            {/* Channel Details */}
                            <div className="space-y-3 mb-4">
                                {channel.config.phoneNumber && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <Smartphone className="w-4 h-4 text-gray-400" />
                                        <span className="text-gray-600 dark:text-gray-400">
                                            {channel.config.phoneNumber}
                                        </span>
                                    </div>
                                )}

                                {channel.webhookUrl && (
                                    <div className="flex items-center gap-2">
                                        <code className="flex-1 text-xs bg-gray-100 dark:bg-gray-900 p-2 rounded text-gray-600 dark:text-gray-400 truncate">
                                            {channel.webhookUrl}
                                        </code>
                                        <button
                                            onClick={() => handleCopyWebhook(channel.webhookUrl!)}
                                            className="p-1.5 text-gray-400 hover:text-blue-600"
                                        >
                                            <Copy className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}

                                {channel.assignedAgent && (
                                    <div className="flex items-center gap-2 text-sm">
                                        <span className="text-gray-500 dark:text-gray-400">Assigned to:</span>
                                        <span className="px-2 py-0.5 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs font-medium">
                                            Agent {channel.assignedAgent}
                                        </span>
                                    </div>
                                )}
                            </div>

                            {/* Stats */}
                            <div className="flex items-center justify-between pt-4 border-t border-gray-100 dark:border-gray-700">
                                <div className="text-sm text-gray-500 dark:text-gray-400">
                                    Last message: <span className="font-medium text-gray-900 dark:text-white">{channel.lastMessage}</span>
                                </div>

                                <button
                                    onClick={() => toast.success('Messages synced')}
                                    className="flex items-center gap-1 text-sm text-blue-600 hover:text-blue-700"
                                >
                                    <RefreshCw className="w-4 h-4" />
                                    Sync
                                </button>
                            </div>
                        </div>
                    );
                })}
            </div>

            {/* How It Works */}
            <div className="bg-gray-50 dark:bg-gray-800/50 rounded-xl p-6 border border-gray-200 dark:border-gray-700">
                <h2 className="text-lg font-semibold text-gray-900 dark:text-white mb-4">
                    How Multi-Channel Works
                </h2>
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
                    <div className="space-y-2">
                        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 font-bold text-sm">1</div>
                        <h3 className="font-medium text-gray-900 dark:text-white">External Message</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            User sends WhatsApp/Slack message to your business number
                        </p>
                    </div>

                    <div className="space-y-2">
                        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 font-bold text-sm">2</div>
                        <h3 className="font-medium text-gray-900 dark:text-white">Backend Routing</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            Backend receives webhook, creates task, routes to Head of Council
                        </p>
                    </div>

                    <div className="space-y-2">
                        <div className="w-8 h-8 rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center text-blue-600 font-bold text-sm">3</div>
                        <h3 className="font-medium text-gray-900 dark:text-white">Agent Processing</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                            AI agents deliberate and respond via same channel (WhatsApp/Slack)
                        </p>
                    </div>
                </div>
            </div>

            {/* Add Channel Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                Add Communication Channel
                            </h2>
                            <button
                                onClick={() => {
                                    setShowAddModal(false);
                                    setSelectedType(null);
                                    setQrCode(null);
                                }}
                                className="text-gray-400 hover:text-gray-600"
                            >
                                ✕
                            </button>
                        </div>

                        <div className="p-6">
                            {!selectedType ? (
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {channelTypes.map((type) => (
                                        <button
                                            key={type.id}
                                            onClick={() => handleConnect(type.id)}
                                            className="flex items-center gap-4 p-4 border border-gray-200 dark:border-gray-700 rounded-xl hover:border-blue-500 dark:hover:border-blue-500 transition-colors text-left"
                                        >
                                            <div className={`w-12 h-12 rounded-lg bg-${type.color}-100 dark:bg-${type.color}-900/30 flex items-center justify-center`}>
                                                <type.icon className={`w-6 h-6 text-${type.color}-600`} />
                                            </div>
                                            <div>
                                                <h3 className="font-semibold text-gray-900 dark:text-white">
                                                    {type.name}
                                                </h3>
                                                <p className="text-sm text-gray-500 dark:text-gray-400">
                                                    {type.description}
                                                </p>
                                            </div>
                                        </button>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center space-y-6">
                                    {qrCode ? (
                                        <div className="space-y-4">
                                            <div className="w-64 h-64 mx-auto bg-white p-4 rounded-xl">
                                                <img src={qrCode} alt="QR Code" className="w-full h-full" />
                                            </div>
                                            <p className="text-gray-600 dark:text-gray-400">
                                                Scan this QR code with WhatsApp on your phone<br />
                                                Settings → Linked Devices → Link a Device
                                            </p>
                                        </div>
                                    ) : (
                                        <div className="space-y-4">
                                            <div className="w-16 h-16 mx-auto rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                                <Power className="w-8 h-8 text-blue-600" />
                                            </div>
                                            <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                                                Configure {selectedType}
                                            </h3>

                                            <div className="max-w-sm mx-auto space-y-4">
                                                <input
                                                    type="text"
                                                    placeholder={`${selectedType} Bot Token`}
                                                    className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white"
                                                />
                                                <button
                                                    onClick={() => toast.success('Configuration saved')}
                                                    className="w-full py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                                                >
                                                    Connect
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    <button
                                        onClick={() => {
                                            setSelectedType(null);
                                            setQrCode(null);
                                        }}
                                        className="text-sm text-gray-500 hover:text-gray-700"
                                    >
                                        ← Back to channels
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}