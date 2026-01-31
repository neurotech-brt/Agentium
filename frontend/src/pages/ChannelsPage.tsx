import { useState, useEffect } from 'react';
import { useQuery, useMutation, useQueryClient } from '@tanstack/react-query';
import { api } from '@/services/api';
import {
    Smartphone,
    Slack,
    Mail,
    MessageCircle,
    Plus,
    Power,
    Settings,
    QrCode,
    Copy,
    CheckCircle,
    AlertCircle,
    RefreshCw,
    Trash2,
    ExternalLink,
    ChevronRight,
    Loader2,
    X
} from 'lucide-react';
import { format } from 'date-fns';
import toast from 'react-hot-toast';
import QRCode from 'qrcode.react';

interface Channel {
    id: string;
    name: string;
    type: 'whatsapp' | 'slack' | 'telegram' | 'email';
    status: 'pending' | 'active' | 'error' | 'disconnected';
    config: {
        phone_number?: string;
        has_credentials: boolean;
        webhook_url?: string;
    };
    routing: {
        default_agent?: string;
        auto_create_tasks: boolean;
        require_approval: boolean;
    };
    stats: {
        received: number;
        sent: number;
        last_message?: string;
    };
}

interface ChannelFormData {
    name: string;
    type: 'whatsapp' | 'slack' | 'telegram' | 'email';
    config: Record<string, string>;
    default_agent_id?: string;
    auto_create_tasks: boolean;
    require_approval: boolean;
}

export function ChannelsPage() {
    const queryClient = useQueryClient();
    const [showAddModal, setShowAddModal] = useState(false);
    const [selectedType, setSelectedType] = useState<string | null>(null);
    const [qrCodeData, setQrCodeData] = useState<string | null>(null);
    const [pollingChannelId, setPollingChannelId] = useState<string | null>(null);

    // Fetch channels
    const { data: channels = [], isLoading } = useQuery({
        queryKey: ['channels'],
        queryFn: async () => {
            const response = await api.get('/channels/');
            return response.data;
        }
    });

    // Create channel mutation
    const createMutation = useMutation({
        mutationFn: async (data: ChannelFormData) => {
            const response = await api.post('/channels/', data);
            return response.data;
        },
        onSuccess: (data) => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            toast.success('Channel created successfully');

            // If WhatsApp, start QR polling
            if (data.type === 'whatsapp') {
                setPollingChannelId(data.id);
                pollForQR(data.id);
            } else {
                setShowAddModal(false);
                setSelectedType(null);
            }
        },
        onError: (error: any) => {
            toast.error(error.response?.data?.detail || 'Failed to create channel');
        }
    });

    // Delete channel mutation
    const deleteMutation = useMutation({
        mutationFn: async (id: string) => {
            await api.delete(`/channels/${id}`);
        },
        onSuccess: () => {
            queryClient.invalidateQueries({ queryKey: ['channels'] });
            toast.success('Channel deleted');
        }
    });

    // Test connection mutation
    const testMutation = useMutation({
        mutationFn: async (id: string) => {
            const response = await api.post(`/channels/${id}/test`);
            return response.data;
        },
        onSuccess: (data) => {
            if (data.success) {
                toast.success('Connection successful!');
            } else {
                toast.error(`Connection failed: ${data.error}`);
            }
            queryClient.invalidateQueries({ queryKey: ['channels'] });
        }
    });

    // Poll for QR code (WhatsApp)
    const pollForQR = async (channelId: string) => {
        try {
            const response = await api.get(`/channels/${channelId}/qr`);
            if (response.data.qr_code) {
                setQrCodeData(response.data.qr_code);
            } else if (response.data.status === 'active') {
                toast.success('WhatsApp connected successfully!');
                setShowAddModal(false);
                setSelectedType(null);
                setQrCodeData(null);
                setPollingChannelId(null);
                queryClient.invalidateQueries({ queryKey: ['channels'] });
                return;
            }

            // Continue polling
            if (pollingChannelId === channelId) {
                setTimeout(() => pollForQR(channelId), 3000);
            }
        } catch (error) {
            console.error('QR polling error:', error);
        }
    };

    // Cleanup polling
    useEffect(() => {
        return () => setPollingChannelId(null);
    }, []);

    const channelTypes = [
        {
            id: 'whatsapp',
            name: 'WhatsApp Business',
            icon: Smartphone,
            description: 'Connect via WhatsApp Business API or WhatsApp Web',
            color: 'green',
            instructions: 'Scan QR code with your phone to pair',
            fields: [
                { name: 'phone_number', label: 'Business Phone Number', type: 'tel', placeholder: '+1234567890' }
            ]
        },
        {
            id: 'slack',
            name: 'Slack',
            icon: Slack,
            description: 'Slack Bot integration for workspace channels',
            color: 'purple',
            instructions: 'Create a Slack app and enter your Bot Token',
            fields: [
                { name: 'bot_token', label: 'Bot Token', type: 'password', placeholder: 'xoxb-...' },
                { name: 'signing_secret', label: 'Signing Secret', type: 'password', placeholder: 'Optional - for verification' }
            ]
        },
        {
            id: 'telegram',
            name: 'Telegram',
            icon: MessageCircle,
            description: 'Telegram Bot API integration',
            color: 'blue',
            instructions: 'Create bot with @BotFather and enter the token',
            fields: [
                { name: 'bot_token', label: 'Bot Token', type: 'password', placeholder: '123456789:ABCdefGHI...' }
            ]
        },
        {
            id: 'email',
            name: 'Email (SMTP/IMAP)',
            icon: Mail,
            description: 'Send and receive emails via SMTP',
            color: 'red',
            instructions: 'Enter your SMTP server details',
            fields: [
                { name: 'smtp_host', label: 'SMTP Host', type: 'text', placeholder: 'smtp.gmail.com' },
                { name: 'smtp_port', label: 'SMTP Port', type: 'number', placeholder: '587' },
                { name: 'smtp_user', label: 'Username', type: 'email', placeholder: 'your@email.com' },
                { name: 'smtp_pass', label: 'Password', type: 'password', placeholder: 'App-specific password' },
                { name: 'from_email', label: 'From Email', type: 'email', placeholder: 'noreply@yourdomain.com' }
            ]
        }
    ];

    const handleCopyWebhook = (url: string) => {
        navigator.clipboard.writeText(url);
        toast.success('Webhook URL copied to clipboard');
    };

    const getStatusColor = (status: string) => {
        const colors = {
            active: 'bg-green-500',
            connected: 'bg-green-500',
            disconnected: 'bg-gray-400',
            error: 'bg-red-500',
            pending: 'bg-yellow-500'
        };
        return colors[status] || 'bg-gray-400';
    };

    const getChannelIcon = (type: string) => {
        const found = channelTypes.find(t => t.id === type);
        return found?.icon || MessageCircle;
    };

    return (
        <div className="max-w-7xl mx-auto">
            {/* Header */}
            <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-4 mb-8">
                <div>
                    <h1 className="text-3xl font-bold text-gray-900 dark:text-white mb-2">
                        Communication Channels
                    </h1>
                    <p className="text-gray-600 dark:text-gray-400">
                        Connect WhatsApp, Slack, Email and other platforms to your AI agents
                    </p>
                </div>

                <button
                    onClick={() => setShowAddModal(true)}
                    className="flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg transition-colors"
                >
                    <Plus className="w-5 h-5" />
                    Add Channel
                </button>
            </div>

            {/* Stats Overview */}
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4 mb-8">
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-gray-900 dark:text-white">
                        {channels.length}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Total Channels</div>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-green-600">
                        {channels.filter(c => c.status === 'active').length}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Active</div>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-blue-600">
                        {channels.reduce((acc, c) => acc + c.stats.received, 0)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Messages Received</div>
                </div>
                <div className="bg-white dark:bg-gray-800 p-4 rounded-xl border border-gray-200 dark:border-gray-700">
                    <div className="text-2xl font-bold text-purple-600">
                        {channels.reduce((acc, c) => acc + c.stats.sent, 0)}
                    </div>
                    <div className="text-sm text-gray-500 dark:text-gray-400">Responses Sent</div>
                </div>
            </div>

            {/* Channels Grid */}
            {isLoading ? (
                <div className="flex items-center justify-center h-64">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600" />
                </div>
            ) : channels.length === 0 ? (
                <div className="text-center py-16 bg-gray-50 dark:bg-gray-800/50 rounded-2xl border border-dashed border-gray-300 dark:border-gray-700">
                    <div className="w-16 h-16 mx-auto rounded-full bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center mb-4">
                        <Plus className="w-8 h-8 text-blue-600" />
                    </div>
                    <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                        No channels connected
                    </h3>
                    <p className="text-gray-600 dark:text-gray-400 mb-6 max-w-md mx-auto">
                        Connect external platforms like WhatsApp or Slack to allow users to interact
                        with your AI agents outside of this dashboard.
                    </p>
                    <button
                        onClick={() => setShowAddModal(true)}
                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg"
                    >
                        Add Your First Channel
                    </button>
                </div>
            ) : (
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                    {channels.map((channel) => {
                        const Icon = getChannelIcon(channel.type);
                        const typeInfo = channelTypes.find(t => t.id === channel.type);

                        return (
                            <div
                                key={channel.id}
                                className="bg-white dark:bg-gray-800 rounded-xl border border-gray-200 dark:border-gray-700 overflow-hidden hover:shadow-lg transition-shadow"
                            >
                                {/* Header */}
                                <div className="p-6 border-b border-gray-200 dark:border-gray-700">
                                    <div className="flex items-start justify-between">
                                        <div className="flex items-center gap-4">
                                            <div className={`w-12 h-12 rounded-xl bg-${typeInfo?.color}-100 dark:bg-${typeInfo?.color}-900/30 flex items-center justify-center`}>
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

                                        <div className="flex gap-2">
                                            <button
                                                onClick={() => testMutation.mutate(channel.id)}
                                                disabled={testMutation.isPending}
                                                className="p-2 text-gray-400 hover:text-blue-600 hover:bg-blue-50 dark:hover:bg-blue-900/20 rounded-lg transition-colors"
                                                title="Test Connection"
                                            >
                                                <RefreshCw className={`w-5 h-5 ${testMutation.isPending ? 'animate-spin' : ''}`} />
                                            </button>

                                            <button
                                                onClick={() => {
                                                    if (confirm('Delete this channel? This cannot be undone.')) {
                                                        deleteMutation.mutate(channel.id);
                                                    }
                                                }}
                                                className="p-2 text-gray-400 hover:text-red-600 hover:bg-red-50 dark:hover:bg-red-900/20 rounded-lg transition-colors"
                                                title="Delete"
                                            >
                                                <Trash2 className="w-5 h-5" />
                                            </button>
                                        </div>
                                    </div>
                                </div>

                                {/* Body */}
                                <div className="p-6 space-y-4">
                                    {/* Webhook URL */}
                                    {channel.config?.webhook_url && (
                                        <div>
                                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 uppercase tracking-wider mb-1.5">
                                                Webhook URL
                                            </label>
                                            <div className="flex gap-2">
                                                <code className="flex-1 text-xs bg-gray-100 dark:bg-gray-900 px-3 py-2 rounded-lg text-gray-600 dark:text-gray-400 truncate font-mono">
                                                    {channel.config.webhook_url}
                                                </code>
                                                <button
                                                    onClick={() => handleCopyWebhook(channel.config.webhook_url!)}
                                                    className="px-3 py-2 bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600 rounded-lg transition-colors"
                                                    title="Copy"
                                                >
                                                    <Copy className="w-4 h-4 text-gray-600 dark:text-gray-400" />
                                                </button>
                                            </div>
                                        </div>
                                    )}

                                    {/* Configuration Info */}
                                    {channel.config?.phone_number && (
                                        <div className="flex items-center gap-3 text-sm">
                                            <Smartphone className="w-4 h-4 text-gray-400" />
                                            <span className="text-gray-600 dark:text-gray-300">
                                                {channel.config.phone_number}
                                            </span>
                                        </div>
                                    )}

                                    {channel.routing?.default_agent && (
                                        <div className="flex items-center gap-3 text-sm">
                                            <Settings className="w-4 h-4 text-gray-400" />
                                            <span className="text-gray-600 dark:text-gray-300">
                                                Default Agent: {channel.routing.default_agent}
                                            </span>
                                        </div>
                                    )}

                                    {/* Stats */}
                                    <div className="flex items-center gap-6 pt-4 border-t border-gray-100 dark:border-gray-700">
                                        <div className="text-sm">
                                            <span className="text-gray-500 dark:text-gray-400">Received: </span>
                                            <span className="font-semibold text-gray-900 dark:text-white">
                                                {channel.stats.received}
                                            </span>
                                        </div>
                                        <div className="text-sm">
                                            <span className="text-gray-500 dark:text-gray-400">Sent: </span>
                                            <span className="font-semibold text-gray-900 dark:text-white">
                                                {channel.stats.sent}
                                            </span>
                                        </div>
                                        {channel.stats.last_message && (
                                            <div className="text-sm text-gray-500 dark:text-gray-400 ml-auto">
                                                Last: {format(new Date(channel.stats.last_message), 'MMM d, h:mm a')}
                                            </div>
                                        )}
                                    </div>
                                </div>

                                {/* Footer Actions */}
                                {channel.status === 'active' && (
                                    <div className="px-6 py-4 bg-gray-50 dark:bg-gray-700/50 border-t border-gray-200 dark:border-gray-700">
                                        <button
                                            onClick={() => window.open(`/channels/${channel.id}/messages`, '_blank')}
                                            className="flex items-center gap-2 text-sm text-blue-600 hover:text-blue-700 font-medium"
                                        >
                                            View Messages
                                            <ChevronRight className="w-4 h-4" />
                                        </button>
                                    </div>
                                )}
                            </div>
                        );
                    })}
                </div>
            )}

            {/* Add Channel Modal */}
            {showAddModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center p-4 z-50 backdrop-blur-sm">
                    <div className="bg-white dark:bg-gray-800 rounded-2xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                        <div className="p-6 border-b border-gray-200 dark:border-gray-700 flex items-center justify-between sticky top-0 bg-white dark:bg-gray-800">
                            <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                                Add Communication Channel
                            </h2>
                            <button
                                onClick={() => {
                                    setShowAddModal(false);
                                    setSelectedType(null);
                                    setQrCodeData(null);
                                    setPollingChannelId(null);
                                }}
                                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
                            >
                                <X className="w-5 h-5 text-gray-500" />
                            </button>
                        </div>

                        <div className="p-6">
                            {!selectedType ? (
                                // Channel Type Selection
                                <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
                                    {channelTypes.map((type) => (
                                        <button
                                            key={type.id}
                                            onClick={() => setSelectedType(type.id)}
                                            className={`flex items-center gap-4 p-4 border-2 rounded-xl transition-all text-left hover:border-blue-500 hover:shadow-md ${selectedType === type.id
                                                    ? 'border-blue-500 bg-blue-50 dark:bg-blue-900/20'
                                                    : 'border-gray-200 dark:border-gray-700'
                                                }`}
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
                                // Configuration Form
                                <ChannelConfigForm
                                    type={selectedType}
                                    typeInfo={channelTypes.find(t => t.id === selectedType)!}
                                    qrCodeData={qrCodeData}
                                    onSubmit={(data) => createMutation.mutate(data)}
                                    isSubmitting={createMutation.isPending}
                                    onBack={() => {
                                        setSelectedType(null);
                                        setQrCodeData(null);
                                    }}
                                />
                            )}
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

// Channel Configuration Form Component
function ChannelConfigForm({
    type,
    typeInfo,
    qrCodeData,
    onSubmit,
    isSubmitting,
    onBack
}: {
    type: string;
    typeInfo: any;
    qrCodeData: string | null;
    onSubmit: (data: any) => void;
    isSubmitting: boolean;
    onBack: () => void;
}) {
    const [formData, setFormData] = useState({
        name: '',
        config: {} as Record<string, string>,
        auto_create_tasks: true,
        require_approval: false
    });

    const handleSubmit = (e: React.FormEvent) => {
        e.preventDefault();
        onSubmit({
            ...formData,
            type,
            config: formData.config
        });
    };

    return (
        <div className="space-y-6">
            <button
                onClick={onBack}
                className="flex items-center gap-2 text-sm text-gray-500 hover:text-gray-700 dark:hover:text-gray-300 mb-4"
            >
                <ChevronRight className="w-4 h-4 rotate-180" />
                Back to channel types
            </button>

            {/* QR Code Display (WhatsApp) */}
            {type === 'whatsapp' && qrCodeData && (
                <div className="text-center space-y-4 p-6 bg-green-50 dark:bg-green-900/20 rounded-xl border border-green-200 dark:border-green-800">
                    <div className="inline-block p-4 bg-white rounded-xl shadow-lg">
                        <QRCode value={qrCodeData} size={256} level="H" />
                    </div>
                    <div className="space-y-2">
                        <h3 className="font-semibold text-green-900 dark:text-green-300">
                            Scan with WhatsApp
                        </h3>
                        <p className="text-sm text-green-700 dark:text-green-400">
                            Open WhatsApp on your phone → Settings → Linked Devices → Link a Device
                        </p>
                        <div className="flex items-center justify-center gap-2 text-sm text-green-600">
                            <Loader2 className="w-4 h-4 animate-spin" />
                            Waiting for connection...
                        </div>
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-6">
                {/* Basic Info */}
                <div>
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-2">
                        Channel Name
                    </label>
                    <input
                        type="text"
                        required
                        value={formData.name}
                        onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                        placeholder={`My ${typeInfo.name}`}
                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                    />
                </div>

                {/* Dynamic Fields based on Channel Type */}
                <div className="space-y-4">
                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300">
                        Configuration
                    </label>
                    {typeInfo.fields.map((field: any) => (
                        <div key={field.name}>
                            <label className="block text-xs font-medium text-gray-500 dark:text-gray-400 mb-1.5">
                                {field.label}
                            </label>
                            <input
                                type={field.type}
                                value={formData.config[field.name] || ''}
                                onChange={(e) => setFormData({
                                    ...formData,
                                    config: { ...formData.config, [field.name]: e.target.value }
                                })}
                                placeholder={field.placeholder}
                                className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-700 text-gray-900 dark:text-white focus:ring-2 focus:ring-blue-500 focus:border-blue-500"
                            />
                        </div>
                    ))}
                </div>

                {/* Routing Options */}
                <div className="space-y-4 p-4 bg-gray-50 dark:bg-gray-700/50 rounded-lg">
                    <h4 className="font-medium text-gray-900 dark:text-white flex items-center gap-2">
                        <Settings className="w-4 h-4" />
                        Routing Options
                    </h4>

                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Auto-create Tasks
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Automatically create tasks from incoming messages
                            </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                checked={formData.auto_create_tasks}
                                onChange={(e) => setFormData({ ...formData, auto_create_tasks: e.target.checked })}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                    </div>

                    <div className="flex items-center justify-between">
                        <div>
                            <p className="text-sm font-medium text-gray-700 dark:text-gray-300">
                                Require Approval
                            </p>
                            <p className="text-xs text-gray-500 dark:text-gray-400">
                                Send sensitive messages to Council for approval first
                            </p>
                        </div>
                        <label className="relative inline-flex items-center cursor-pointer">
                            <input
                                type="checkbox"
                                checked={formData.require_approval}
                                onChange={(e) => setFormData({ ...formData, require_approval: e.target.checked })}
                                className="sr-only peer"
                            />
                            <div className="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-blue-300 dark:peer-focus:ring-blue-800 rounded-full peer dark:bg-gray-700 peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all dark:border-gray-600 peer-checked:bg-blue-600"></div>
                        </label>
                    </div>
                </div>

                <div className="flex gap-3 pt-4">
                    <button
                        type="button"
                        onClick={onBack}
                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        disabled={isSubmitting}
                        className="flex-1 flex items-center justify-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed text-white rounded-lg transition-colors"
                    >
                        {isSubmitting ? (
                            <>
                                <Loader2 className="w-4 h-4 animate-spin" />
                                Connecting...
                            </>
                        ) : (
                            <>
                                <CheckCircle className="w-4 h-4" />
                                Connect {typeInfo.name}
                            </>
                        )}
                    </button>
                </div>
            </form>
        </div>
    );
}