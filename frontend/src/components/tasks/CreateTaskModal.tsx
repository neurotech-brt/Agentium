import React, { useState } from 'react';
import { X, FileText } from 'lucide-react';

interface CreateTaskModalProps {
    onConfirm: (data: { title: string; description: string; priority: string; task_type: string }) => Promise<void>;
    onClose: () => void;
}

export const CreateTaskModal: React.FC<CreateTaskModalProps> = ({ onConfirm, onClose }) => {
    const [title, setTitle] = useState('');
    const [description, setDescription] = useState('');
    const [priority, setPriority] = useState('normal');
    const [taskType, setTaskType] = useState('execution');
    const [isLoading, setIsLoading] = useState(false);
    const [error, setError] = useState<string | null>(null);

    const handleSubmit = async (e: React.FormEvent) => {
        e.preventDefault();
        setIsLoading(true);
        setError(null);

        try {
            await onConfirm({ title, description, priority, task_type: taskType });
            onClose();
        } catch (err: any) {
            setError(err.message || 'Failed to create task');
        } finally {
            setIsLoading(false);
        }
    };

    return (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
            <div className="bg-gray-800 rounded-xl shadow-2xl w-full max-w-lg border border-gray-700 max-h-[90vh] overflow-y-auto">
                <div className="flex justify-between items-center p-6 border-b border-gray-700 sticky top-0 bg-gray-800 z-10">
                    <h2 className="text-xl font-bold text-white flex items-center gap-2">
                        <FileText className="w-6 h-6 text-blue-400" />
                        Create New Task
                    </h2>
                    <button onClick={onClose} className="text-gray-400 hover:text-white">
                        <X className="w-5 h-5" />
                    </button>
                </div>

                <form onSubmit={handleSubmit} className="p-6 space-y-4">
                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">Task Title</label>
                        <input
                            type="text"
                            value={title}
                            onChange={(e) => setTitle(e.target.value)}
                            className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="e.g., Analyze market trends"
                            required
                        />
                    </div>

                    <div>
                        <label className="block text-gray-300 text-sm font-medium mb-1">Description</label>
                        <textarea
                            value={description}
                            onChange={(e) => setDescription(e.target.value)}
                            rows={4}
                            className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            placeholder="Describe what needs to be done..."
                            required
                        />
                    </div>

                    <div className="grid grid-cols-2 gap-4">
                        <div>
                            <label className="block text-gray-300 text-sm font-medium mb-1">Priority</label>
                            <select
                                value={priority}
                                onChange={(e) => setPriority(e.target.value)}
                                className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="low">Low</option>
                                <option value="normal">Normal</option>
                                <option value="urgent">Urgent</option>
                                <option value="critical">Critical</option>
                            </select>
                        </div>
                        <div>
                            <label className="block text-gray-300 text-sm font-medium mb-1">Type</label>
                            <select
                                value={taskType}
                                onChange={(e) => setTaskType(e.target.value)}
                                className="w-full bg-gray-700 text-white rounded p-2.5 focus:outline-none focus:ring-2 focus:ring-blue-500"
                            >
                                <option value="execution">Execution</option>
                                <option value="research">Research</option>
                                <option value="creative">Creative</option>
                            </select>
                        </div>
                    </div>

                    {error && (
                        <div className="text-red-400 text-sm p-2 bg-red-900/20 rounded border border-red-800/50">
                            {error}
                        </div>
                    )}

                    <div className="flex justify-end gap-3 pt-4 border-t border-gray-700 mt-6">
                        <button
                            type="button"
                            onClick={onClose}
                            className="px-4 py-2 text-gray-300 hover:text-white transition-colors"
                        >
                            Cancel
                        </button>
                        <button
                            type="submit"
                            disabled={isLoading}
                            className="px-4 py-2 bg-blue-600 hover:bg-blue-500 text-white rounded-lg transition-colors font-medium"
                        >
                            {isLoading ? 'Creating...' : 'Create Task'}
                        </button>
                    </div>
                </form>
            </div>
        </div>
    );
};
