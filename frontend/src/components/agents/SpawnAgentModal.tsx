import React, { useState } from 'react';
import { Agent } from '../../types';
import { X, UserPlus } from 'lucide-react';

interface SpawnAgentModalProps {
    parent: Agent;
    onConfirm: (name: string, childType: 'council_member' | 'lead_agent' | 'task_agent') => Promise<void>;
    onClose: () => void;
}

export const SpawnAgentModal: React.FC<SpawnAgentModalProps> = ({ parent, onConfirm, onClose }) => {
    const [name, setName] = useState('');
    const [childType, setChildType] = useState<string>('');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const getAllowedTypes = () => {
        switch (parent.agent_type) {
            case 'head_of_council':
                return [
                    { value: 'council_member', label: 'Council Member' },
                    { value: 'lead_agent', label: 'Lead Agent' }
                ];
            case 'council_member':
                return []; // Council members cannot spawn directly
            case 'lead_agent':
                return [{ value: 'task_agent', label: 'Task Agent' }];
            default:
                return [];
        }
    };

    const allowedTypes = getAllowedTypes();

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        if (!name || !childType) return;

        setIsLoading(true);
        setError(null);
        try {
            await onConfirm(name, childType as any);
            onClose();
        } catch (err: any) {
            setError(err.response?.data?.detail || 'Failed to spawn agent');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-md border border-gray-700">
                <div className="flex justify-between items-center p-6 border-b border-gray-700">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <UserPlus className="w-6 h-6 text-blue-400" />
                        Spawn New Agent
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div className="bg-blue-900/20 text-blue-200 p-3 rounded text-sm mb-4">
                        Spawning subordinate for <strong>{parent.name}</strong> ({parent.agent_type})
                    </div>

                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">Agent Name</label>
                        <input
                            type="text"
                            value={name}
                            onChange={(e) => setName(e.target.value)}
                            placeholder="e.g. Research Specialist"
                            className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">Agent Type</label>
                        <select
                            value={childType}
                            onChange={(e) => setChildType(e.target.value)}
                            className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            required
                        >
                            <option value="">Select a role...</option>
                            {allowedTypes.map(type => (
                                <option key={type.value} value={type.value}>{type.label}</option>
                            ))}
                        </select>
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm p-2 bg-red-900/20 rounded border border-red-800/50">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading || !childType || !name}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            {isLoading ? 'Spawning...' : 'Spawn Agent'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
