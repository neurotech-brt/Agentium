import React, { useEffect, useState } from 'react';
import { ModelConfig, modelsService } from '../services/models';
import { ModelConfigForm } from '../components/models/ModelConfigForm';
import toast from 'react-hot-toast';

export const ModelsPage: React.FC = () => {
    const [configs, setConfigs] = useState<ModelConfig[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [error, setError] = useState<string | null>(null);
    const [isEditing, setIsEditing] = useState(false);
    const [editingConfig, setEditingConfig] = useState<ModelConfig | undefined>(undefined);

    useEffect(() => {
        loadConfigs();
    }, []);

    const loadConfigs = async () => {
        try {
            setIsLoading(true);
            const data = await modelsService.getConfigs();
            setConfigs(data);
        } catch (err) {
            console.error(err);
            setError('Failed to load configurations');
        } finally {
            setIsLoading(false);
        }
    };

    const handleAddNew = () => {
        setEditingConfig(undefined);
        setIsEditing(true);
    };

    const handleEdit = (config: ModelConfig) => {
        setEditingConfig(config);
        setIsEditing(true);
    };

    const handleDelete = async (id: string) => {
        if (!window.confirm('Are you sure you want to delete this configuration?')) return;

        try {
            await modelsService.deleteConfig(id);
            await loadConfigs();
            toast.success('Configuration deleted');
        } catch (err) {
            console.error(err);
            // toast auto-handled
        }
    };

    const handleSetDefault = async (id: string, e: React.MouseEvent) => {
        e.stopPropagation();
        try {
            await modelsService.setDefault(id);
            await loadConfigs();
            toast.success('Default configuration updated');
        } catch (err) {
            console.error(err);
            // toast auto-handled
        }
    };

    const handleSave = async (config: ModelConfig) => {
        setIsEditing(false);
        await loadConfigs();
    };

    return (
        <div className="p-6">
            <div className="flex justify-between items-center mb-6">
                <h1 className="text-3xl font-bold text-white">AI Models</h1>
                <button
                    onClick={handleAddNew}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors"
                    disabled={isEditing}
                >
                    <span className="text-xl">+</span> Add New Model
                </button>
            </div>

            {error && (
                <div className="bg-red-900/50 text-red-200 p-4 rounded-lg border border-red-800 mb-6">
                    {error}
                </div>
            )}

            {isEditing ? (
                <div className="max-w-2xl mx-auto">
                    <ModelConfigForm
                        initialConfig={editingConfig}
                        onSave={handleSave}
                        onCancel={() => setIsEditing(false)}
                    />
                </div>
            ) : (
                <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                    {isLoading ? (
                        <div className="text-gray-400">Loading configurations...</div>
                    ) : configs.length === 0 ? (
                        <div className="col-span-full text-center py-12 bg-gray-800/50 rounded-lg border border-gray-700">
                            <p className="text-xl text-gray-300 mb-4">No model configurations found</p>
                            <p className="text-gray-500">Add an API key to start using the chat.</p>
                        </div>
                    ) : (
                        configs.map(config => (
                            <div
                                key={config.id}
                                className={`bg-gray-800 rounded-lg p-6 border transition-all ${config.is_default
                                    ? 'border-blue-500 shadow-lg shadow-blue-900/20'
                                    : 'border-gray-700 hover:border-gray-600'
                                    }`}
                            >
                                <div className="flex justify-between items-start mb-4">
                                    <div>
                                        <h3 className="text-xl font-bold text-white mb-1 flex items-center gap-2">
                                            {config.config_name}
                                            {config.is_default && (
                                                <span className="text-xs bg-blue-600 text-white px-2 py-0.5 rounded-full font-medium">
                                                    DEFAULT
                                                </span>
                                            )}
                                        </h3>
                                        <div className="text-sm text-gray-400 capitalize bg-gray-700 px-2 py-0.5 rounded inline-block">
                                            {config.provider.replace('_', ' ')}
                                        </div>
                                    </div>
                                    <div className="flex space-x-2">
                                        <button
                                            onClick={() => handleEdit(config)}
                                            className="text-gray-400 hover:text-white p-1"
                                            title="Edit"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                                            </svg>
                                        </button>
                                        <button
                                            onClick={() => handleDelete(config.id)}
                                            className="text-gray-400 hover:text-red-400 p-1"
                                            title="Delete"
                                        >
                                            <svg className="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                                                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 7l-.867 12.142A2 2 0 0116.138 21H7.862a2 2 0 01-1.995-1.858L5 7m5 4v6m4-6v6m1-10V4a1 1 0 00-1-1h-4a1 1 0 00-1 1v3M4 7h16" />
                                            </svg>
                                        </button>
                                    </div>
                                </div>

                                <div className="space-y-3 text-sm text-gray-400 mb-6">
                                    <div className="flex justify-between">
                                        <span>Model:</span>
                                        <span className="text-white font-mono">{config.default_model}</span>
                                    </div>
                                    <div className="flex justify-between">
                                        <span>Status:</span>
                                        <span className={`${config.status === 'active' ? 'text-green-400' :
                                            config.status === 'testing' ? 'text-yellow-400' :
                                                'text-red-400'
                                            } capitalize`}>
                                            {config.status}
                                        </span>
                                    </div>
                                    {config.usage && (
                                        <div className="flex justify-between border-t border-gray-700 pt-2 mt-2">
                                            <span>Usage (7d):</span>
                                            <span className="text-white">
                                                {config.usage.requests} reqs / {config.usage.tokens_total.toLocaleString()} toks
                                            </span>
                                        </div>
                                    )}
                                </div>

                                {!config.is_default && (
                                    <button
                                        onClick={(e) => handleSetDefault(config.id, e)}
                                        className="w-full py-2 border border-gray-600 text-gray-300 rounded hover:bg-gray-700 transition-colors text-sm"
                                    >
                                        Set as Default
                                    </button>
                                )}
                            </div>
                        ))
                    )}
                </div>
            )}
        </div>
    );
};
