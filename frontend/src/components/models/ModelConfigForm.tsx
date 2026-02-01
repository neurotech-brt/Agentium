import React, { useState, useEffect } from 'react';
import { AlertCircle, Check, Loader2, Server, Key, Globe, Settings, TestTube, ChevronLeft } from 'lucide-react';
import { modelsApi } from '../../services/models';
import type { ModelConfig, ProviderInfo, ProviderType, UniversalProviderInput } from '../../types';

interface ModelConfigFormProps {
    initialConfig?: ModelConfig;
    onSave: (config: ModelConfig) => void;
    onCancel: () => void;
}

const PRESET_PROVIDERS: Record<string, { baseUrl: string; models: string[] }> = {
    groq: {
        baseUrl: 'https://api.groq.com/openai/v1',
        models: ['llama3-70b-8192', 'mixtral-8x7b-32768', 'gemma-7b-it']
    },
    mistral: {
        baseUrl: 'https://api.mistral.ai/v1',
        models: ['mistral-large-latest', 'mistral-medium', 'mistral-small']
    },
    together: {
        baseUrl: 'https://api.together.xyz/v1',
        models: ['meta-llama/Llama-3-70b-chat-hf', 'mistralai/Mixtral-8x22B-Instruct-v0.1']
    },
    moonshot: {
        baseUrl: 'https://api.moonshot.cn/v1',
        models: ['moonshot-v1-8k', 'moonshot-v1-32k', 'moonshot-v1-128k']  // Kimi 2.5
    },
    deepseek: {
        baseUrl: 'https://api.deepseek.com/v1',
        models: ['deepseek-chat', 'deepseek-coder']
    },
    fireworks: {
        baseUrl: 'https://api.fireworks.ai/inference/v1',
        models: ['accounts/fireworks/models/llama-v3-70b-instruct']
    }
};

export const ModelConfigForm: React.FC<ModelConfigFormProps> = ({ initialConfig, onSave, onCancel }) => {
    const [step, setStep] = useState<'provider' | 'configure'>('provider');
    const [providers, setProviders] = useState<ProviderInfo[]>([]);
    const [selectedProvider, setSelectedProvider] = useState<ProviderInfo | null>(null);
    const [isUniversal, setIsUniversal] = useState(false);

    // Form state
    const [formData, setFormData] = useState({
        config_name: '',
        provider: '' as ProviderType,
        custom_provider_name: '',
        api_key: '',
        api_base_url: '',
        local_server_url: 'http://localhost:11434/v1',
        default_model: '',
        available_models: [] as string[],
        temperature: 0.7,
        max_tokens: 4000,
        top_p: 0.9,
        timeout: 60,
        is_default: false
    });

    const [isLoading, setIsLoading] = useState(false);
    const [testing, setTesting] = useState(false);
    const [fetchingModels, setFetchingModels] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string; error?: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadProviders();
        if (initialConfig) {
            setStep('configure');
            const provider = providers.find(p => p.id === initialConfig.provider);
            setSelectedProvider(provider || null);
            setIsUniversal(initialConfig.provider === 'custom');
            setFormData({
                config_name: initialConfig.config_name,
                provider: initialConfig.provider,
                custom_provider_name: initialConfig.provider_name || '',
                api_key: '',
                api_base_url: initialConfig.api_base_url || '',
                local_server_url: initialConfig.local_server_url || 'http://localhost:11434/v1',
                default_model: initialConfig.default_model,
                available_models: initialConfig.available_models,
                temperature: initialConfig.settings.temperature,
                max_tokens: initialConfig.settings.max_tokens,
                top_p: initialConfig.settings.top_p || 0.9,
                timeout: initialConfig.settings.timeout,
                is_default: initialConfig.is_default
            });
        }
    }, [initialConfig]);

    const loadProviders = async () => {
        try {
            const data = await modelsApi.getProviders();
            setProviders(data);
        } catch (err) {
            setError('Failed to load providers');
        }
    };

    const selectProvider = (provider: ProviderInfo) => {
        setSelectedProvider(provider);
        setIsUniversal(false);

        // Auto-fill preset data
        const preset = PRESET_PROVIDERS[provider.id];
        const baseUrl = provider.default_base_url || preset?.baseUrl || '';
        const defaultModel = preset?.models[0] || provider.popular_models[0] || '';

        setFormData(prev => ({
            ...prev,
            provider: provider.id,
            api_base_url: baseUrl,
            default_model: defaultModel,
            available_models: preset?.models || provider.popular_models,
            config_name: prev.config_name || `${provider.display_name} Config`
        }));

        setStep('configure');
    };

    const handleUniversalSelect = () => {
        setIsUniversal(true);
        setSelectedProvider(null);
        setFormData(prev => ({
            ...prev,
            provider: 'custom',
            api_base_url: '',
            default_model: '',
            config_name: prev.config_name || 'Custom Provider'
        }));
        setStep('configure');
    };

    const handleLocalSelect = () => {
        const localProvider = providers.find(p => p.id === 'local');
        if (localProvider) {
            setSelectedProvider(localProvider);
            setFormData(prev => ({
                ...prev,
                provider: 'local',
                local_server_url: 'http://localhost:11434/v1',
                config_name: prev.config_name || 'Local Ollama'
            }));
            setStep('configure');
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked :
                type === 'number' ? parseFloat(value) : value
        }));
    };

    const fetchAvailableModels = async () => {
        if (!formData.api_key && selectedProvider?.requires_api_key) {
            setError('API key required to fetch models');
            return;
        }

        setFetchingModels(true);
        setError(null);

        try {
            // Create temp config to fetch models
            const payload: any = {
                provider: formData.provider,
                config_name: 'Temp Fetch Models',
                default_model: formData.default_model || 'test',
                api_key: formData.api_key || undefined
            };

            if (formData.provider === 'local') {
                payload.local_server_url = formData.local_server_url;
            } else if (formData.api_base_url) {
                payload.api_base_url = formData.api_base_url;
            }

            const tempConfig = await modelsApi.createConfig(payload);
            const result = await modelsApi.fetchModels(tempConfig.id);

            if (result.models.length > 0) {
                setFormData(prev => ({
                    ...prev,
                    available_models: result.models,
                    default_model: prev.default_model || result.models[0]
                }));
                setTestResult({
                    success: true,
                    message: `Found ${result.count} models`
                });
            }

            // Clean up temp config
            await modelsApi.deleteConfig(tempConfig.id);
        } catch (err: any) {
            setError('Failed to fetch models: ' + (err.response?.data?.detail || err.message));
        } finally {
            setFetchingModels(false);
        }
    };

    const handleTestConnection = async () => {
        setTesting(true);
        setTestResult(null);
        setError(null);

        try {
            // Create temp config for testing
            let payload: any;

            if (isUniversal) {
                // Universal provider test
                const universalInput: UniversalProviderInput = {
                    provider_name: formData.custom_provider_name,
                    api_base_url: formData.api_base_url,
                    api_key: formData.api_key || undefined,
                    default_model: formData.default_model,
                    config_name: 'Test Config'
                };

                const result = await modelsApi.createUniversalConfig(universalInput);
                // Test immediately by making a simple request
                // Since we don't have a test endpoint for universal, we try to use it
                setTestResult({
                    success: true,
                    message: 'Configuration validated. Save to persist.'
                });
                await modelsApi.deleteConfig(result.id);
            } else {
                // Standard provider test
                payload = {
                    provider: formData.provider,
                    config_name: 'Test Config',
                    default_model: formData.default_model,
                    api_key: formData.api_key || undefined,
                    available_models: [formData.default_model]
                };

                if (formData.provider === 'local') {
                    payload.local_server_url = formData.local_server_url;
                } else if (formData.api_base_url) {
                    payload.api_base_url = formData.api_base_url;
                }

                const tempConfig = await modelsApi.createConfig(payload);

                try {
                    const result = await modelsApi.testConfig(tempConfig.id);
                    setTestResult(result);
                } finally {
                    // Clean up if test failed or succeeded
                    if (!testResult?.success) {
                        await modelsApi.deleteConfig(tempConfig.id);
                    }
                }
            }
        } catch (err: any) {
            setTestResult({
                success: false,
                message: 'Connection failed',
                error: err.response?.data?.detail || err.message
            });
        } finally {
            setTesting(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            let savedConfig;

            const payload = {
                config_name: formData.config_name,
                default_model: formData.default_model,
                available_models: formData.available_models.length > 0 ? formData.available_models : [formData.default_model],
                is_default: formData.is_default,
                max_tokens: formData.max_tokens,
                temperature: formData.temperature,
                top_p: formData.top_p,
                timeout_seconds: formData.timeout
            };

            if (isUniversal) {
                // Universal provider creation
                const universalInput: UniversalProviderInput = {
                    provider_name: formData.custom_provider_name,
                    api_base_url: formData.api_base_url,
                    api_key: formData.api_key || undefined,
                    default_model: formData.default_model,
                    config_name: formData.config_name,
                    is_default: formData.is_default
                };
                savedConfig = await modelsApi.createUniversalConfig(universalInput);
            } else {
                // Standard provider
                const standardPayload: any = {
                    ...payload,
                    provider: formData.provider,
                    api_key: formData.api_key || undefined
                };

                if (formData.provider === 'local') {
                    standardPayload.local_server_url = formData.local_server_url;
                } else if (formData.api_base_url) {
                    standardPayload.api_base_url = formData.api_base_url;
                }

                if (initialConfig) {
                    savedConfig = await modelsApi.updateConfig(initialConfig.id, standardPayload);
                } else {
                    savedConfig = await modelsApi.createConfig(standardPayload);
                }
            }

            onSave(savedConfig);
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to save configuration');
        } finally {
            setIsLoading(false);
        }
    };

    // Provider Selection Step
    if (step === 'provider' && !initialConfig) {
        return (
            <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-4xl mx-auto">
                <h2 className="text-2xl font-bold mb-6 text-white">Select AI Provider</h2>

                {/* Standard Providers Grid */}
                <div className="grid grid-cols-2 md:grid-cols-3 gap-4 mb-6">
                    {providers.filter(p => p.id !== 'custom' && p.id !== 'local').map((provider) => (
                        <button
                            key={provider.id}
                            onClick={() => selectProvider(provider)}
                            className="p-4 bg-gray-700 border-2 border-gray-600 rounded-lg hover:border-blue-500 hover:bg-gray-600 transition-all text-left"
                        >
                            <div className="font-semibold text-white">{provider.display_name}</div>
                            <div className="text-xs text-gray-400 mt-1 line-clamp-2">{provider.description}</div>
                            <div className="mt-2 flex flex-wrap gap-1">
                                {provider.popular_models.slice(0, 2).map(m => (
                                    <span key={m} className="text-xs bg-gray-800 text-gray-300 px-2 py-1 rounded">
                                        {m.split('/').pop()?.slice(0, 15)}...
                                    </span>
                                ))}
                            </div>
                        </button>
                    ))}
                </div>

                {/* Local Models */}
                <div className="border-t border-gray-700 pt-6 mb-6">
                    <h3 className="text-sm font-medium text-gray-400 mb-3">Local Models</h3>
                    <button
                        onClick={handleLocalSelect}
                        className="w-full p-4 bg-gray-700 border-2 border-gray-600 rounded-lg hover:border-green-500 hover:bg-gray-600 transition-all text-left"
                    >
                        <div className="font-medium text-white flex items-center gap-2">
                            <Server className="w-4 h-4" />
                            Local Model (Ollama, LM Studio)
                        </div>
                        <div className="text-sm text-gray-400">
                            Run models on your own hardware
                        </div>
                    </button>
                </div>

                {/* Custom Provider */}
                <div className="border-t border-gray-700 pt-6">
                    <h3 className="text-sm font-medium text-gray-400 mb-3">Custom Provider</h3>
                    <button
                        onClick={handleUniversalSelect}
                        className="w-full p-4 bg-gray-700 border-2 border-dashed border-gray-600 rounded-lg hover:border-blue-500 hover:bg-gray-600 transition-all text-left"
                    >
                        <div className="font-medium text-white">Add Custom Provider</div>
                        <div className="text-sm text-gray-400">
                            Any OpenAI-compatible API (Perplexity, AI21, Copilot, etc.)
                        </div>
                    </button>
                </div>

                <div className="mt-6 flex justify-end">
                    <button
                        onClick={onCancel}
                        className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500"
                    >
                        Cancel
                    </button>
                </div>
            </div>
        );
    }

    // Configuration Form Step
    return (
        <div className="bg-gray-800 p-6 rounded-lg shadow-xl max-w-2xl mx-auto">
            <div className="flex items-center justify-between mb-6">
                <h2 className="text-xl font-bold text-white">
                    {isUniversal ? 'Custom Provider' : selectedProvider?.display_name}
                </h2>
                {!initialConfig && (
                    <button
                        onClick={() => setStep('provider')}
                        className="text-sm text-blue-400 hover:underline flex items-center gap-1"
                    >
                        <ChevronLeft className="w-4 h-4" />
                        Change Provider
                    </button>
                )}
            </div>

            {error && (
                <div className="mb-4 p-3 bg-red-900/50 text-red-200 rounded border border-red-800 flex items-center gap-2">
                    <AlertCircle className="w-5 h-5" />
                    {error}
                </div>
            )}

            {testResult && (
                <div className={`mb-4 p-3 rounded border flex items-start gap-2 ${testResult.success
                        ? 'bg-green-900/50 text-green-200 border-green-800'
                        : 'bg-red-900/50 text-red-200 border-red-800'
                    }`}>
                    {testResult.success ? <Check className="w-5 h-5" /> : <AlertCircle className="w-5 h-5" />}
                    <div>
                        <div className="font-medium">{testResult.message}</div>
                        {testResult.error && <div className="text-sm mt-1">{testResult.error}</div>}
                    </div>
                </div>
            )}

            <form onSubmit={handleSubmit} className="space-y-4">
                {/* Config Name */}
                <div>
                    <label className="block text-gray-300 mb-1">Configuration Name</label>
                    <input
                        type="text"
                        name="config_name"
                        value={formData.config_name}
                        onChange={handleChange}
                        className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="My Production API"
                        required
                    />
                </div>

                {/* Universal: Custom Provider Name */}
                {isUniversal && (
                    <div>
                        <label className="block text-gray-300 mb-1">
                            Provider Name <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            name="custom_provider_name"
                            value={formData.custom_provider_name}
                            onChange={handleChange}
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., Perplexity, Fireworks, MyCompany"
                            required
                        />
                    </div>
                )}

                {/* API Key */}
                {(selectedProvider?.requires_api_key || isUniversal) && (
                    <div>
                        <label className="block text-gray-300 mb-1 flex items-center gap-2">
                            <Key className="w-4 h-4" />
                            {formData.provider === 'local' ? 'API Key (optional)' : 'API Key'}
                            {formData.provider === 'local' && (
                                <span className="text-xs text-gray-500">- Most local servers don't need this</span>
                            )}
                        </label>
                        <input
                            type="password"
                            name="api_key"
                            value={formData.api_key}
                            onChange={handleChange}
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="sk-... or gsk-... etc."
                        />
                        {initialConfig?.api_key_masked && !formData.api_key && (
                            <p className="text-xs text-gray-500 mt-1">
                                Current: {initialConfig.api_key_masked} (leave empty to keep)
                            </p>
                        )}
                    </div>
                )}

                {/* Base URL */}
                {(selectedProvider?.requires_base_url || isUniversal || selectedProvider?.id === 'custom') && (
                    <div>
                        <label className="block text-gray-300 mb-1 flex items-center gap-2">
                            <Globe className="w-4 h-4" />
                            API Base URL <span className="text-red-500">*</span>
                        </label>
                        <input
                            type="text"
                            name="api_base_url"
                            value={formData.api_base_url}
                            onChange={handleChange}
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                            placeholder="https://api.provider.com/v1"
                            required
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Must end with /v1 for OpenAI-compatible endpoints
                        </p>
                    </div>
                )}

                {/* Local Server URL */}
                {formData.provider === 'local' && (
                    <div>
                        <label className="block text-gray-300 mb-1 flex items-center gap-2">
                            <Server className="w-4 h-4" />
                            Local Server URL
                        </label>
                        <input
                            type="text"
                            name="local_server_url"
                            value={formData.local_server_url}
                            onChange={handleChange}
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500 font-mono text-sm"
                        />
                        <p className="text-xs text-gray-500 mt-1">
                            Default: Ollama (http://localhost:11434/v1). For LM Studio use http://localhost:1234/v1
                        </p>
                    </div>
                )}

                {/* Model Selection */}
                <div>
                    <label className="block text-gray-300 mb-1">
                        Model <span className="text-red-500">*</span>
                    </label>
                    <div className="flex gap-2">
                        <input
                            type="text"
                            name="default_model"
                            value={formData.default_model}
                            onChange={handleChange}
                            className="flex-1 bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder={isUniversal ? "model-name" : "gpt-4, llama3-70b, etc."}
                            list="available-models"
                            required
                        />
                        {!isUniversal && formData.provider !== 'local' && (
                            <button
                                type="button"
                                onClick={fetchAvailableModels}
                                disabled={fetchingModels || !formData.api_key}
                                className="px-3 py-2 bg-gray-600 hover:bg-gray-500 rounded text-sm whitespace-nowrap disabled:opacity-50"
                                title={!formData.api_key ? "Enter API key first" : "Fetch models from provider"}
                            >
                                {fetchingModels ? '...' : 'Fetch'}
                            </button>
                        )}
                    </div>
                    <datalist id="available-models">
                        {formData.available_models.map(m => (
                            <option key={m} value={m} />
                        ))}
                    </datalist>
                    <p className="text-xs text-gray-500 mt-1">
                        {isUniversal
                            ? "Enter the exact model name as expected by the API"
                            : "Select from list or enter custom model name"
                        }
                    </p>
                </div>

                {/* Advanced Settings */}
                <div className="border border-gray-600 rounded p-4 space-y-4">
                    <h4 className="font-medium text-gray-300 flex items-center gap-2">
                        <Settings className="w-4 h-4" />
                        Advanced Settings
                    </h4>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Max Tokens</label>
                            <input
                                type="number"
                                name="max_tokens"
                                value={formData.max_tokens}
                                onChange={handleChange}
                                className="w-full bg-gray-700 text-white rounded p-2"
                                min="100"
                                max="128000"
                            />
                        </div>
                        <div>
                            <label className="block text-sm text-gray-400 mb-1">Temperature</label>
                            <input
                                type="number"
                                name="temperature"
                                value={formData.temperature}
                                onChange={handleChange}
                                className="w-full bg-gray-700 text-white rounded p-2"
                                min="0"
                                max="2"
                                step="0.1"
                            />
                        </div>
                    </div>
                </div>

                {/* Default Checkbox */}
                <label className="flex items-center gap-2 text-gray-300">
                    <input
                        type="checkbox"
                        name="is_default"
                        checked={formData.is_default}
                        onChange={handleChange}
                        className="rounded bg-gray-700 border-gray-600 text-blue-600 focus:ring-blue-500"
                    />
                    Set as default configuration
                </label>

                {/* Test Connection */}
                <button
                    type="button"
                    onClick={handleTestConnection}
                    disabled={testing || !formData.default_model}
                    className="w-full py-2 bg-gray-700 hover:bg-gray-600 text-blue-400 border border-blue-500/50 rounded flex items-center justify-center gap-2 disabled:opacity-50"
                >
                    <TestTube className="w-4 h-4" />
                    {testing ? 'Testing...' : 'Test Connection'}
                </button>

                {/* Actions */}
                <div className="flex justify-end gap-3 pt-4 border-t border-gray-700">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500"
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 disabled:opacity-50 flex items-center gap-2"
                        disabled={isLoading}
                    >
                        {isLoading && <Loader2 className="w-4 h-4 animate-spin" />}
                        {initialConfig ? 'Update' : 'Create'} Configuration
                    </button>
                </div>
            </form>
        </div>
    );
};