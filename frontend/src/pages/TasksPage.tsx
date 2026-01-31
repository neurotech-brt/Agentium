import React, { useEffect, useState } from 'react';
import { Task } from '../types';
import { tasksService, CreateTaskRequest } from '../services/tasks';
import { TaskCard } from '../components/tasks/TaskCard';
import { CreateTaskModal } from '../components/tasks/CreateTaskModal';
import { Plus, Filter } from 'lucide-react';
import toast from 'react-hot-toast';

export const TasksPage: React.FC = () => {
    const [tasks, setTasks] = useState<Task[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [showCreateModal, setShowCreateModal] = useState(false);
    const [filterStatus, setFilterStatus] = useState<string>('');

    useEffect(() => {
        loadTasks();
    }, [filterStatus]);

    const loadTasks = async () => {
        try {
            setIsLoading(true);
            const data = await tasksService.getTasks({ status: filterStatus || undefined });
            setTasks(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCreateTask = async (data: any) => {
        // Map form data to request type safely
        const requestData: CreateTaskRequest = {
            title: data.title,
            description: data.description,
            priority: data.priority,
            task_type: data.task_type
        };

        await tasksService.createTask(requestData);
        await loadTasks();
        toast.success('Task created successfully');
    };

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Tasks</h1>
                    <p className="text-gray-400">Monitor and manage agent operations</p>
                </div>

                <button
                    onClick={() => setShowCreateModal(true)}
                    className="bg-blue-600 hover:bg-blue-500 text-white px-4 py-2 rounded-lg flex items-center gap-2 transition-colors shadow-lg shadow-blue-900/20"
                >
                    <Plus className="w-5 h-5" />
                    New Task
                </button>
            </div>

            {/* Filters */}
            <div className="mb-6 flex items-center gap-4">
                <div className="flex items-center gap-2 text-gray-400">
                    <Filter className="w-4 h-4" />
                    <span className="text-sm font-medium">Filter Status:</span>
                </div>
                <div className="flex gap-2">
                    {['', 'pending', 'deliberating', 'executing', 'completed', 'failed'].map(status => (
                        <button
                            key={status}
                            onClick={() => setFilterStatus(status)}
                            className={`px-3 py-1 rounded-full text-xs font-medium transition-colors capitalize ${filterStatus === status
                                ? 'bg-blue-600 text-white'
                                : 'bg-gray-800 text-gray-400 hover:bg-gray-700'
                                }`}
                        >
                            {status || 'All'}
                        </button>
                    ))}
                </div>
            </div>

            <div className="flex-1 overflow-auto bg-gray-900/50 rounded-xl border border-gray-800 p-6">
                {isLoading ? (
                    <div className="text-center text-gray-500 mt-10">Loading tasks...</div>
                ) : tasks.length === 0 ? (
                    <div className="text-center text-gray-500 mt-10">
                        {filterStatus ? `No tasks found with status "${filterStatus}"` : 'No tasks found. Create one to get started.'}
                    </div>
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-4">
                        {tasks.map(task => (
                            <TaskCard key={task.id} task={task} />
                        ))}
                    </div>
                )}
            </div>

            {showCreateModal && (
                <CreateTaskModal
                    onConfirm={handleCreateTask}
                    onClose={() => setShowCreateModal(false)}
                />
            )}
        </div>
    );
};
