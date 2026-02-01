import React, { useEffect, useState } from 'react';
import {
    Plus,
    Trash2,
    Edit2,
    Check,
    AlertCircle,
    Server,
    Activity,
    RefreshCw,
    Cpu,
    Globe,
    Key
} from 'lucide-react';
import { modelsApi } from '../services/models';
import { ModelConfigForm } from '../components/models/ModelConfigForm';
import type { ModelConfig } from '../types';

export const ModelsPage: React.FC = () => {
    const [configs, setConfigs] = useState<ModelConfig[]>([]);
    const [loading, setLoading] = useState(true);
    const [showForm, setShowForm] = useState(false);
    const [editingConfig, setEditingConfig] = useState<ModelConfig | null>(null);
    const [testingId, setTestingId] = useState<string | null>(null);
    const [deletingId, setDeletingId] = useState<string | null>(null);

    useEffect(() => {
        loadConfigs();
    }, []);

    const loadConfigs = async () => {
        try {
            const data = await modelsApi.getConfigs();
            setConfigs(data);
        } catch (err) {
            console.error('Failed to load configs:', err);
        } finally {
            setLoading(false);
        }
    };

    const handleDelete = async (id: string) => {
        if (!confirm('Delete this configuration?')) return;
        setDeletingId(id);
        try {
            await modelsApi.deleteConfig(id);
            await loadConfigs();
        } catch (err) {
            alert('Failed to delete');
        } finally {
            setDeletingId(null);
        }
    };

    const handleSetDefault = async (id: string) => {
        try {
            await modelsApi.setDefault(id);
            await loadConfigs();
        } catch (err) {
            alert('Failed to set default');
        }
    };

    const handleTest = async (id: string) => {
        setTestingId(id);
        try {
            const result = await modelsApi.testConfig(id);
            alert(result.success
                ? `✅ Connection successful!\nLatency: ${result.latency_ms}ms\nModel: ${result.model}`
                : `❌ Connection failed: ${result.error}`
            );
        } catch (err) {
            alert('Test failed');
        } finally {
            setTestingId(null);
        }
    };

    const handleFetchModels = async (id: string) => {
        try {
            const result = await modelsApi.fetchModels(id);
            alert(`Found ${result.count} models:\n${result.models.slice(0, 10).join('\n')}${result.count > 10 ? '\n...and more' : ''}`);
            await loadConfigs();
        } catch (err: any) {
            alert('Failed to fetch models: ' + err.message);
        }
    };

    const getProviderIcon = (provider: string) => {
        switch (provider) {
            case 'local': return <Server className="w-4 h-4" />;
            case 'custom': return <Globe className="w-4 h-4" />;
            default: return <Cpu className="w-4 h-4" />;
        }
    };

    const getProviderColor = (provider: string) => {
        switch (provider) {
            case 'openai': return 'text-green-400';
            case 'anthropic': return 'text-orange-400';
            case 'gemini': return 'text-blue-400';
            case 'groq': return 'text-pink-400';
            case 'mistral': return 'text-purple-400';
            case 'local': return 'text-gray-400';
            case 'custom': return 'text-yellow-400';
            default: return 'text-blue-400';
        }
    };

    if (loading) {
        return (
            <div className="min-h-screen bg-gray-900 p-8 text-center text-gray-300">
                <RefreshCw className="w-8 h-8 animate-spin mx-auto mb-4" />
                Loading configurations...
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-900 p-8">
            <div className="max-w-6xl mx-auto">
                {/* Header */}
                <div className="flex justify-between items-center mb-8">
                    <div>
                        <h1 className="text-3xl font-bold text-white">Model Configurations</h1>
                        <p className="text-gray-400 mt-2">
                            Manage AI providers: OpenAI, Anthropic, Groq, Mistral, Gemini, Moonshot (Kimi),
                            Local models, and any OpenAI-compatible API
                        </p>
                    </div>
                    <button
                        onClick={() => {
                            setEditingConfig(null);
                            setShowForm(true);
                        }}
                        className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 flex items-center gap-2 transition-colors"
                    >
                        <Plus className="w-4 h-4" />
                        Add Provider
                    </button>
                </div>

                {/* Modal */}
                {showForm && (
                    <div className="fixed inset-0 bg-black/70 backdrop-blur-sm flex items-center justify-center z-50 p-4">
                        <div className="w-full max-w-2xl max-h-[90vh] overflow-y-auto">
                            <ModelConfigForm
                                onSave={(config) => {
                                    setShowForm(false);
                                    setEditingConfig(null);
                                    loadConfigs();
                                }}
                                onCancel={() => {
                                    setShowForm(false);
                                    setEditingConfig(null);
                                }}
                                initialConfig={editingConfig}
                            />
                        </div>
                    </div>
                )}

                {/* Configurations List */}
                <div className="space-y-4">
                    {configs.map((config) => (
                        <div
                            key={config.id}
                            className={`border rounded-lg p-6 transition-all ${config.is_default
                                ? 'border-blue-500 bg-blue-900/20'
                                : 'border-gray-700 bg-gray-800 hover:border-gray-600'
                                }`}
                        >
                            <div className="flex justify-between items-start">
                                <div className="flex-1">
                                    {/* Title Row */}
                                    <div className="flex items-center gap-3 flex-wrap">
                                        <h3 className="text-lg font-semibold text-white">
                                            {config.config_name}
                                        </h3>

                                        {config.is_default && (
                                            <span className="px-2 py-1 bg-blue-900/50 text-blue-300 text-xs font-medium rounded border border-blue-700">
                                                Default
                                            </span>
                                        )}

                                        <span className={`px-2 py-1 text-xs rounded border ${config.status === 'active'
                                            ? 'bg-green-900/30 text-green-400 border-green-700' :
                                            config.status === 'testing'
                                                ? 'bg-yellow-900/30 text-yellow-400 border-yellow-700' :
                                                config.status === 'error'
                                                    ? 'bg-red-900/30 text-red-400 border-red-700'
                                                    : 'bg-gray-700 text-gray-400 border-gray-600'
                                            }`}>
                                            {config.status}
                                        </span>

                                        {config.api_key_masked && (
                                            <span className="flex items-center gap-1 text-xs text-gray-500">
                                                <Key className="w-3 h-3" />
                                                {config.api_key_masked}
                                            </span>
                                        )}
                                    </div>

                                    {/* Provider & Model Info */}
                                    <div className="flex items-center gap-4 mt-3 text-sm">
                                        <span className={`flex items-center gap-1 font-medium ${getProviderColor(config.provider)}`}>
                                            {getProviderIcon(config.provider)}
                                            {config.provider_name || config.provider}
                                        </span>
                                        <span className="text-gray-400 font-mono bg-gray-900 px-2 py-1 rounded">
                                            {config.default_model}
                                        </span>
                                        {config.api_base_url && (
                                            <span className="text-xs text-gray-500 truncate max-w-xs font-mono">
                                                {config.api_base_url}
                                            </span>
                                        )}
                                        {config.local_server_url && (
                                            <span className="text-xs text-gray-500 truncate max-w-xs font-mono">
                                                {config.local_server_url}
                                            </span>
                                        )}
                                    </div>

                                    {/* Available Models Tags */}
                                    {config.available_models.length > 0 && (
                                        <div className="mt-3 flex flex-wrap gap-2">
                                            {config.available_models.slice(0, 5).map(model => (
                                                <span
                                                    key={model}
                                                    className={`text-xs px-2 py-1 rounded ${model === config.default_model
                                                        ? 'bg-blue-900/50 text-blue-300 border border-blue-700'
                                                        : 'bg-gray-700 text-gray-400'
                                                        }`}
                                                >
                                                    {model.split('/').pop()?.slice(0, 25)}
                                                </span>
                                            ))}
                                            {config.available_models.length > 5 && (
                                                <span className="text-xs text-gray-500 px-2 py-1">
                                                    +{config.available_models.length - 5} more
                                                </span>
                                            )}
                                        </div>
                                    )}

                                    {/* Usage Stats */}
                                    <div className="mt-4 flex items-center gap-6 text-sm text-gray-400 border-t border-gray-700 pt-3">
                                        <span className="flex items-center gap-1">
                                            <Activity className="w-4 h-4" />
                                            {config.total_usage.requests.toLocaleString()} requests
                                        </span>
                                        <span>
                                            {config.total_usage.tokens.toLocaleString()} tokens
                                        </span>
                                        <span className="font-mono text-green-400">
                                            ${config.total_usage.cost_usd.toFixed(4)}
                                        </span>
                                        {config.last_tested && (
                                            <span className="text-xs text-gray-500">
                                                Tested: {new Date(config.last_tested).toLocaleString()}
                                            </span>
                                        )}
                                    </div>
                                </div>

                                {/* Action Buttons */}
                                <div className="flex items-center gap-1 ml-4">
                                    {!config.is_default && (
                                        <button
                                            onClick={() => handleSetDefault(config.id)}
                                            className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-900/30 rounded transition-colors"
                                            title="Set as default"
                                        >
                                            <Check className="w-4 h-4" />
                                        </button>
                                    )}

                                    <button
                                        onClick={() => handleTest(config.id)}
                                        disabled={testingId === config.id}
                                        className="p-2 text-gray-400 hover:text-green-400 hover:bg-green-900/30 rounded transition-colors disabled:opacity-50"
                                        title="Test connection"
                                    >
                                        <RefreshCw className={`w-4 h-4 ${testingId === config.id ? 'animate-spin' : ''}`} />
                                    </button>

                                    <button
                                        onClick={() => handleFetchModels(config.id)}
                                        className="p-2 text-gray-400 hover:text-purple-400 hover:bg-purple-900/30 rounded transition-colors"
                                        title="Fetch available models"
                                    >
                                        <Server className="w-4 h-4" />
                                    </button>

                                    <button
                                        onClick={() => {
                                            setEditingConfig(config);
                                            setShowForm(true);
                                        }}
                                        className="p-2 text-gray-400 hover:text-blue-400 hover:bg-blue-900/30 rounded transition-colors"
                                        title="Edit configuration"
                                    >
                                        <Edit2 className="w-4 h-4" />
                                    </button>

                                    <button
                                        onClick={() => handleDelete(config.id)}
                                        disabled={deletingId === config.id}
                                        className="p-2 text-gray-400 hover:text-red-400 hover:bg-red-900/30 rounded transition-colors disabled:opacity-50"
                                        title="Delete configuration"
                                    >
                                        <Trash2 className="w-4 h-4" />
                                    </button>
                                </div>
                            </div>

                            {/* Error Message */}
                            {config.status === 'error' && (
                                <div className="mt-4 p-3 bg-red-900/30 text-red-400 text-sm rounded border border-red-800 flex items-center gap-2">
                                    <AlertCircle className="w-4 h-4" />
                                    Configuration error - please check API key and connection settings
                                </div>
                            )}
                        </div>
                    ))}

                    {/* Empty State */}
                    {configs.length === 0 && (
                        <div className="text-center py-16 border-2 border-dashed border-gray-700 rounded-lg">
                            <Server className="w-12 h-12 text-gray-600 mx-auto mb-4" />
                            <h3 className="text-lg font-medium text-gray-300 mb-2">No configurations yet</h3>
                            <p className="text-gray-500 mb-6 max-w-md mx-auto">
                                Add your first AI provider to get started with Agentium.
                                Supports OpenAI, Anthropic, Groq, Mistral, Gemini, Moonshot (Kimi 2.5),
                                local models, and any OpenAI-compatible API.
                            </p>
                            <button
                                onClick={() => setShowForm(true)}
                                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-500 flex items-center gap-2 mx-auto"
                            >
                                <Plus className="w-4 h-4" />
                                Add Your First Provider
                            </button>
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
};

export default ModelsPage;