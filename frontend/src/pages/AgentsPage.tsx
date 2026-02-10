import React, { useEffect, useState } from 'react';
import { Agent } from '../types';
import { agentsService } from '../services/agents';
import { AgentTree } from '../components/agents/AgentTree';
import { SpawnAgentModal } from '../components/agents/SpawnAgentModal';
import { LayoutGrid, List, Users, AlertCircle, Loader2 } from 'lucide-react';
import { toast } from 'react-hot-toast';

// Valid agent types for type checking
const VALID_AGENT_TYPES = ['head_of_council', 'council_member', 'lead_agent', 'task_agent'] as const;

const AGENT_TYPE_LABELS: Record<string, string> = {
    head_of_council: 'Head of Council',
    council_member: 'Council Member',
    lead_agent: 'Lead Agent',
    task_agent: 'Task Agent',
};

const AGENT_TYPE_COLORS: Record<string, { bg: string; text: string; dot: string }> = {
    head_of_council: { bg: 'bg-violet-50', text: 'text-violet-700', dot: 'bg-violet-500' },
    council_member: { bg: 'bg-blue-50', text: 'text-blue-700', dot: 'bg-blue-500' },
    lead_agent: { bg: 'bg-emerald-50', text: 'text-emerald-700', dot: 'bg-emerald-500' },
    task_agent: { bg: 'bg-slate-100', text: 'text-slate-600', dot: 'bg-slate-400' },
};

export const AgentsPage: React.FC = () => {
    const [agents, setAgents] = useState<Agent[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [viewMode, setViewMode] = useState<'tree' | 'list'>('tree');
    const [spawnParent, setSpawnParent] = useState<Agent | null>(null);

    useEffect(() => {
        loadAgents();
    }, []);

    const loadAgents = async () => {
        try {
            setIsLoading(true);
            const data = await agentsService.getAgents();

            // SAFETY: Normalize agent data to ensure all required fields exist
            const normalizedAgents = (data || []).map(agent => {
                const rawType = agent.agent_type;
                const validType = VALID_AGENT_TYPES.includes(rawType as any)
                    ? rawType
                    : 'task_agent';

                return {
                    ...agent,
                    subordinates: Array.isArray(agent.subordinates) ? agent.subordinates : [],
                    stats: agent.stats || { tasks_completed: 0, tasks_failed: 0, success_rate: 0 },
                    status: agent.status || 'unknown',
                    name: agent.name || 'Unnamed Agent',
                    agent_type: validType as Agent['agent_type'],
                    agentium_id: agent.agentium_id || agent.id || 'unknown'
                };
            }) as Agent[];

            setAgents(normalizedAgents);
        } catch (err) {
            console.error('Failed to load agents:', err);
            toast.error('Failed to load agents');
        } finally {
            setIsLoading(false);
        }
    };

    const handleSpawn = async (name: string, childType: 'council_member' | 'lead_agent' | 'task_agent') => {
        if (!spawnParent) return;
        try {
            await agentsService.spawnAgent(spawnParent.agentium_id, {
                child_type: childType,
                name
            });
            await loadAgents();
            toast.success('Agent spawned successfully');
        } catch (err) {
            console.error(err);
            throw err;
        }
    };

    const handleTerminate = async (agent: Agent) => {
        if (!window.confirm(`Are you sure you want to terminate ${agent.name}?`)) return;

        try {
            await agentsService.terminateAgent(agent.agentium_id, 'Manual termination by Sovereign');
            await loadAgents();
            toast.success('Agent terminated');
        } catch (err) {
            console.error(err);
            toast.error('Failed to terminate agent');
        }
    };

    // Build the tree with safety checks
    const agentsMap = new Map<string, Agent>();
    agents.forEach(a => {
        if (a && a.agentium_id) {
            agentsMap.set(a.agentium_id, a);
        }
    });

    const headOfCouncil = agents.find(a => a.agent_type === 'head_of_council');

    return (
        <div
            className="p-6 h-full flex flex-col"
            style={{ background: '#ffffff', minHeight: '100%' }}
        >
            {/* ── Header ─────────────────────────────────────────────── */}
            <div className="flex justify-between items-start mb-6">
                <div>
                    <div className="flex items-center gap-2 mb-1">
                        <Users className="w-5 h-5 text-slate-400" />
                        <span className="text-xs font-semibold tracking-widest uppercase text-slate-400">
                            Workforce
                        </span>
                    </div>
                    <h1 className="text-2xl font-bold text-slate-900 leading-tight">
                        Agent Hierarchy
                    </h1>
                    <p className="text-sm text-slate-500 mt-0.5">
                        Manage your AI workforce
                    </p>
                </div>

                {/* View toggle */}
                <div
                    className="flex rounded-lg overflow-hidden border border-slate-200"
                    style={{ background: '#f8fafc' }}
                >
                    <button
                        onClick={() => setViewMode('tree')}
                        title="Tree view"
                        className={[
                            'flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors',
                            viewMode === 'tree'
                                ? 'bg-white text-slate-900 shadow-sm border-r border-slate-200'
                                : 'text-slate-500 hover:text-slate-700 border-r border-slate-200',
                        ].join(' ')}
                    >
                        <LayoutGrid className="w-4 h-4" />
                        <span>Tree</span>
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        title="List view"
                        className={[
                            'flex items-center gap-1.5 px-3 py-2 text-sm font-medium transition-colors',
                            viewMode === 'list'
                                ? 'bg-white text-slate-900 shadow-sm'
                                : 'text-slate-500 hover:text-slate-700',
                        ].join(' ')}
                    >
                        <List className="w-4 h-4" />
                        <span>List</span>
                    </button>
                </div>
            </div>

            {/* ── Content area ───────────────────────────────────────── */}
            <div
                className="flex-1 overflow-auto rounded-xl border border-slate-200 p-6"
                style={{ background: '#ffffff' }}
            >
                {isLoading ? (
                    <div className="flex flex-col items-center justify-center h-40 gap-3 text-slate-400">
                        <Loader2 className="w-6 h-6 animate-spin" />
                        <span className="text-sm">Loading agents…</span>
                    </div>

                ) : agents.length === 0 ? (
                    <div className="flex flex-col items-center justify-center h-40 gap-2 text-slate-400">
                        <Users className="w-8 h-8 opacity-40" />
                        <span className="text-sm">No agents found. System not initialized?</span>
                    </div>

                ) : viewMode === 'tree' ? (
                    headOfCouncil ? (
                        <AgentTree
                            agent={headOfCouncil}
                            agentsMap={agentsMap}
                            onSpawn={setSpawnParent}
                            onTerminate={handleTerminate}
                        />
                    ) : (
                        <div className="flex items-center gap-2 text-red-600 text-sm">
                            <AlertCircle className="w-4 h-4 flex-shrink-0" />
                            <span>Head of Council not found in agent list.</span>
                        </div>
                    )

                ) : (
                    /* ── List / Grid view ─────────────────────────────── */
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-3">
                        {agents.map(agent => {
                            const colors = AGENT_TYPE_COLORS[agent.agent_type] ?? AGENT_TYPE_COLORS.task_agent;
                            const label = AGENT_TYPE_LABELS[agent.agent_type] ?? agent.agent_type;

                            return (
                                <div
                                    key={agent.id || agent.agentium_id}
                                    className="rounded-xl border border-slate-200 p-4 bg-white hover:border-slate-300 hover:shadow-sm transition-all"
                                >
                                    {/* Agent name + type badge */}
                                    <div className="flex items-start justify-between gap-2 mb-3">
                                        <h3 className="text-sm font-semibold text-slate-900 leading-snug">
                                            {agent.name}
                                        </h3>
                                        <span
                                            className={[
                                                'inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs font-medium whitespace-nowrap flex-shrink-0',
                                                colors.bg,
                                                colors.text,
                                            ].join(' ')}
                                        >
                                            <span className={`w-1.5 h-1.5 rounded-full ${colors.dot}`} />
                                            {label}
                                        </span>
                                    </div>

                                    {/* ID */}
                                    <p className="text-xs text-slate-400 font-mono truncate">
                                        {agent.agentium_id}
                                    </p>
                                </div>
                            );
                        })}
                    </div>
                )}
            </div>

            {spawnParent && (
                <SpawnAgentModal
                    parent={spawnParent}
                    onConfirm={handleSpawn}
                    onClose={() => setSpawnParent(null)}
                />
            )}
        </div>
    );
};