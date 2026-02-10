import React from 'react';
import { Agent } from '../../types';
import { Shield, Brain, Users, Terminal, Activity, Zap } from 'lucide-react';

interface AgentCardProps {
    agent: Agent;
    onSpawn: (agent: Agent) => void;
    onTerminate: (agent: Agent) => void;
}

export const AgentCard: React.FC<AgentCardProps> = ({ agent, onSpawn, onTerminate }) => {
    // SAFETY: Handle undefined agent
    if (!agent) {
        return null;
    }

    const isTerminated = agent.status === 'terminated';
    const isHead = agent.agent_type === 'head_of_council';

    // SAFETY: Ensure subordinates is an array
    const subordinateCount = Array.isArray(agent.subordinates) ? agent.subordinates.length : 0;

    // SAFETY: Ensure stats exists
    const tasksCompleted = agent.stats?.tasks_completed ?? 0;

    const getTypeIcon = () => {
        switch (agent.agent_type) {
            case 'head_of_council': return <Shield className="w-5 h-5 text-purple-400" />;
            case 'council_member': return <Users className="w-5 h-5 text-blue-400" />;
            case 'lead_agent': return <Brain className="w-5 h-5 text-green-400" />;
            case 'task_agent': return <Terminal className="w-5 h-5 text-yellow-400" />;
            default: return <Activity className="w-5 h-5 text-gray-400" />;
        }
    };

    const getTypeLabel = () => {
        return agent.agent_type?.replace(/_/g, ' ').replace(/\b\w/g, l => l.toUpperCase()) || 'Unknown';
    };

    const getStatusColor = () => {
        switch (agent.status) {
            case 'active': return 'bg-green-500/10 text-green-400 border-green-500/20';
            case 'working': return 'bg-yellow-500/10 text-yellow-400 border-yellow-500/20';
            case 'deliberating': return 'bg-blue-500/10 text-blue-400 border-blue-500/20';
            case 'terminated': return 'bg-red-500/10 text-red-400 border-red-500/20';
            default: return 'bg-gray-500/10 text-gray-400 border-gray-500/20';
        }
    };

    return (
        <div className={`
            bg-gray-800 rounded-lg border p-4 w-full max-w-sm hover:shadow-lg transition-shadow
            ${isTerminated ? 'opacity-60 border-gray-700' : 'border-gray-700 hover:border-blue-500/50'}
        `}>
            <div className="flex justify-between items-start mb-3">
                <div className="flex items-center gap-3">
                    <div className="p-2 bg-gray-700 rounded-lg">
                        {getTypeIcon()}
                    </div>
                    <div>
                        <h3 className="text-white font-medium flex items-center gap-2">
                            {agent.name || 'Unnamed Agent'}
                            <span className="text-xs text-gray-500 font-mono">#{agent.agentium_id || '???'}</span>
                        </h3>
                        <p className="text-xs text-gray-400">{getTypeLabel()}</p>
                    </div>
                </div>
                <div className={`px-2 py-0.5 rounded text-xs font-medium border ${getStatusColor()} capitalize`}>
                    {agent.status || 'unknown'}
                </div>
            </div>

            {/* Stats / Info */}
            <div className="grid grid-cols-2 gap-2 mb-4 text-xs">
                <div className="bg-gray-700/50 p-2 rounded">
                    <span className="text-gray-400 block">Task Success</span>
                    <span className="text-white font-medium">{tasksCompleted}</span>
                </div>
                <div className="bg-gray-700/50 p-2 rounded">
                    <span className="text-gray-400 block">Subordinates</span>
                    <span className="text-white font-medium">{subordinateCount}</span>
                </div>
            </div>

            {/* Actions */}
            <div className="flex gap-2 mt-2 pt-3 border-t border-gray-700">
                {!isTerminated && agent.agent_type !== 'task_agent' && (
                    <button
                        onClick={() => onSpawn(agent)}
                        className="flex-1 px-3 py-1.5 bg-blue-600/20 text-blue-400 rounded hover:bg-blue-600/30 text-xs font-medium transition-colors flex items-center justify-center gap-1.5"
                    >
                        <Zap className="w-3 h-3" />
                        Spawn
                    </button>
                )}
                {!isTerminated && !isHead && (
                    <button
                        onClick={() => onTerminate(agent)}
                        className="px-3 py-1.5 bg-red-600/20 text-red-400 rounded hover:bg-red-600/30 text-xs font-medium transition-colors"
                    >
                        Terminate
                    </button>
                )}
            </div>
        </div>
    );
};