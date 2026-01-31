import React, { useState, useEffect } from 'react';
import { ModelConfig, ModelConfigCreate, ProviderInfo, modelsService } from '../../services/models';

interface ModelConfigFormProps {
    initialConfig?: ModelConfig;
    onSave: (config: ModelConfig) => void;
    onCancel: () => void;
}

export const ModelConfigForm: React.FC<ModelConfigFormProps> = ({ initialConfig, onSave, onCancel }) => {
    const [providers, setProviders] = useState<ProviderInfo[]>([]);
    const [formData, setFormData] = useState<ModelConfigCreate>({
        config_name: '',
        provider: 'openai',
        api_key: '',
        default_model: '',
        available_models: [],
        temperature: 0.7,
        max_tokens: 4000,
        is_default: false
    });
    const [isLoading, setIsLoading] = useState(false);
    const [testResult, setTestResult] = useState<{ success: boolean; message: string } | null>(null);
    const [error, setError] = useState<string | null>(null);

    useEffect(() => {
        loadProviders();
        if (initialConfig) {
            setFormData({
                config_name: initialConfig.config_name,
                provider: initialConfig.provider,
                api_key: '', // Don't show existing key
                default_model: initialConfig.default_model,
                available_models: initialConfig.available_models,
                temperature: initialConfig.settings.temperature,
                max_tokens: initialConfig.settings.max_tokens,
                is_default: initialConfig.is_default
            });
        }
    }, [initialConfig]);

    const loadProviders = async () => {
        try {
            const data = await modelsService.getProviders();
            setProviders(data);
        } catch (err) {
            console.error('Failed to load providers', err);
            setError('Failed to load providers');
        }
    };

    const handleChange = (e: React.ChangeEvent<HTMLInputElement | HTMLSelectElement>) => {
        const { name, value, type } = e.target;
        setFormData(prev => ({
            ...prev,
            [name]: type === 'checkbox' ? (e.target as HTMLInputElement).checked :
                type === 'number' ? parseFloat(value) : value
        }));

        // Update default models when provider changes
        if (name === 'provider') {
            const provider = providers.find(p => p.id === value);
            if (provider && provider.default_models.length > 0) {
                setFormData(prev => ({
                    ...prev,
                    [name]: value,
                    default_model: provider.default_models[0],
                    available_models: provider.default_models
                }));
            }
        }
    };

    const handleTestConnection = async () => {
        if (!initialConfig && !formData.api_key) {
            setTestResult({ success: false, message: 'API Key is required for testing new configs' });
            return;
        }

        setIsLoading(true);
        setTestResult(null);

        try {
            // Need to save first to test, or have a specific test endpoint that takes raw data
            // For now, if it's new, we might need to rely on the save flow, OR 
            // since the backend test endpoint expects a config_id, we can't test without saving first.
            // Wait, the Requirement said "Test Connection" button.
            // Let's look at the backend... 
            // The backend `test_config` takes `config_id`.
            // So we must save potentially first? 
            // Or maybe we treat "Test Connection" as "Save & Test"?
            // A common pattern is to allow creating a temporary config or just validating the key.
            // But based on current backend, we need an ID.
            // Let's just implement Save first, then Test.
            // Or, we can modify the form to "Save & Test".

            // Actually, for user experience, "Test Connection" usually implies checking before final commit.
            // But if the backend only supports testing saved configs, we might have to save first.
            // Let's assume we save it first, and if it fails, the user can edit/delete.
            // BUT, strictly speaking for UI, let's keep it simple: 
            // If it's an existing config, we can test it.
            // If it's new, we might strictly need to create it first.

            if (initialConfig) {
                const result = await modelsService.testConfig(initialConfig.id);
                setTestResult({ success: result.success, message: result.message });
            } else {
                setTestResult({ success: false, message: 'Please save the configuration first to test connection.' });
            }
        } catch (err) {
            setTestResult({ success: false, message: 'Connection test failed' });
        } finally {
            setIsLoading(false);
        }
    };

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            let savedConfig;
            if (initialConfig) {
                savedConfig = await modelsService.updateConfig(initialConfig.id, formData);
            } else {
                savedConfig = await modelsService.createConfig(formData);
            }
            onSave(savedConfig);
        } catch (err) {
            console.error(err);
            setError('Failed to save configuration');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="bg-gray-800 p-6 rounded-lg shadow-xl">
            <h2 className="text-xl font-bold mb-4 text-white">
                {initialConfig ? 'Edit Configuration' : 'Add New Configuration'}
            </h2>

            <form onSubmit={handleSubmit} className="space-y-4">
                <div>
                    <label className="block text-gray-300 mb-1">Provider</label>
                    <select
                        name="provider"
                        value={formData.provider}
                        onChange={handleChange}
                        className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        disabled={!!initialConfig}
                    >
                        {providers.map(p => (
                            <option key={p.id} value={p.id}>{p.name}</option>
                        ))}
                    </select>
                </div>

                <div>
                    <label className="block text-gray-300 mb-1">Configuration Name</label>
                    <input
                        type="text"
                        name="config_name"
                        value={formData.config_name}
                        onChange={handleChange}
                        className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="e.g., Production OpenAI"
                        required
                    />
                </div>

                <div>
                    <label className="block text-gray-300 mb-1">API Key</label>
                    <input
                        type="password"
                        name="api_key"
                        value={formData.api_key}
                        onChange={handleChange}
                        className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder={initialConfig ? '(Leave blank to keep existing)' : 'sk-...'}
                    />
                </div>

                <div>
                    <label className="block text-gray-300 mb-1">Default Model</label>
                    <input
                        type="text"
                        name="default_model"
                        value={formData.default_model}
                        onChange={handleChange}
                        className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        required
                    />
                </div>

                <div className="grid grid-cols-2 gap-4">
                    <div>
                        <label className="block text-gray-300 mb-1">Temperature</label>
                        <input
                            type="number"
                            name="temperature"
                            value={formData.temperature}
                            onChange={handleChange}
                            step="0.1"
                            min="0"
                            max="2"
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                    <div>
                        <label className="block text-gray-300 mb-1">Max Tokens</label>
                        <input
                            type="number"
                            name="max_tokens"
                            value={formData.max_tokens}
                            onChange={handleChange}
                            className="w-full bg-gray-700 text-white rounded p-2 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        />
                    </div>
                </div>

                <div className="flex items-center space-x-2">
                    <input
                        type="checkbox"
                        name="is_default"
                        checked={formData.is_default}
                        onChange={handleChange}
                        className="form-checkbox h-5 w-5 text-blue-600 rounded focus:ring-blue-500 bg-gray-700 border-gray-600"
                    />
                    <label className="text-gray-300">Set as Default Configuration</label>
                </div>

                {error && (
                    <div className="p-3 bg-red-900/50 text-red-200 rounded border border-red-800">
                        {error}
                    </div>
                )}

                {testResult && (
                    <div className={`p-3 rounded border ${testResult.success ? 'bg-green-900/50 text-green-200 border-green-800' : 'bg-red-900/50 text-red-200 border-red-800'}`}>
                        {testResult.message}
                    </div>
                )}

                <div className="flex justify-end space-x-3 mt-6">
                    <button
                        type="button"
                        onClick={onCancel}
                        className="px-4 py-2 bg-gray-600 text-white rounded hover:bg-gray-500 transition-colors"
                        disabled={isLoading}
                    >
                        Cancel
                    </button>
                    {initialConfig && (
                        <button
                            type="button"
                            onClick={handleTestConnection}
                            className="px-4 py-2 bg-yellow-600 text-white rounded hover:bg-yellow-500 transition-colors"
                            disabled={isLoading}
                        >
                            Test Connection
                        </button>
                    )}
                    <button
                        type="submit"
                        className="px-4 py-2 bg-blue-600 text-white rounded hover:bg-blue-500 transition-colors"
                        disabled={isLoading}
                    >
                        {isLoading ? 'Saving...' : 'Save Configuration'}
                    </button>
                </div>
            </form>
        </div>
    );
};
