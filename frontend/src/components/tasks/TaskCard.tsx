import React from 'react';
import { Task } from '../../types';
import { Clock, User } from 'lucide-react';

interface TaskCardProps {
    task: Task;
}

export const TaskCard: React.FC<TaskCardProps> = ({ task }) => {
    const getStatusColor = () => {
        switch (task.status) {
            case 'pending': return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
            case 'deliberating': return 'bg-purple-500/10 text-purple-400 border-purple-500/20';
            case 'executing': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            case 'completed': return 'bg-green-500/10 text-green-400 border-green-500/20';
            case 'failed': return 'bg-red-500/10 text-red-400 border-red-500/20';
            default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
        }
    };

    const getPriorityColor = () => {
        switch (task.priority) {
            case 'critical': return 'text-red-500';
            case 'urgent': return 'text-orange-500';
            case 'normal': return 'text-blue-500';
            case 'low': return 'text-gray-500';
            default: return 'text-gray-500';
        }
    };

    return (
        <div className="bg-gray-800 rounded-lg border border-gray-700 p-4 hover:border-gray-600 transition-colors">
            <div className="flex justify-between items-start mb-2">
                <div className={`text-xs font-bold uppercase tracking-wider ${getPriorityColor()}`}>
                    {task.priority} Priority
                </div>
                <div className={`px-2 py-0.5 rounded text-xs font-medium border ${getStatusColor()} capitalize`}>
                    {task.status}
                </div>
            </div>

            <h3 className="text-white font-bold mb-2 line-clamp-2">{task.title}</h3>
            <p className="text-gray-400 text-sm mb-4 line-clamp-3">{task.description}</p>

            <div className="flex justify-between items-center text-xs text-gray-500 border-t border-gray-700 pt-3">
                <div className="flex items-center gap-1">
                    <Clock className="w-3 h-3" />
                    {new Date(task.created_at).toLocaleDateString()}
                </div>

                {task.assigned_agents.task_agents.length > 0 && (
                    <div className="flex items-center gap-1 text-blue-400">
                        <User className="w-3 h-3" />
                        {task.assigned_agents.task_agents.length} Agent(s)
                    </div>
                )}
            </div>

            {/* Progress bar if executing */}
            {task.progress > 0 && task.progress < 100 && (
                <div className="mt-3 w-full bg-gray-700 rounded-full h-1.5 overflow-hidden">
                    <div
                        className="bg-blue-500 h-full rounded-full transition-all duration-500"
                        style={{ width: `${task.progress}%` }}
                    />
                </div>
            )}
        </div>
    );
};
