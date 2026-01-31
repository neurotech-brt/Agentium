import React, { useEffect, useState } from 'react';
import { Agent } from '../types';
import { agentsService } from '../services/agents';
import { AgentTree } from '../components/agents/AgentTree';
import { SpawnAgentModal } from '../components/agents/SpawnAgentModal';
import { LayoutGrid, List } from 'lucide-react';
import { toast } from 'react-hot-toast'; // Assuming it's available or we'll use window.alert

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
            setAgents(data);
        } catch (err) {
            console.error(err);
            // toast.error('Failed to load agents');
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
            throw err; // Re-throw for modal to handle
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
            // toast.error handled globally
        }
    };

    // Build the tree
    const agentsMap = new Map<string, Agent>();
    agents.forEach(a => agentsMap.set(a.agentium_id, a)); // Using agentium_id for cleaner linking? Backend uses IDs or AgentiumIDs? 
    // Backend routes use agentium_id (e.g. 0xx). But relationships might use UUIDs.
    // Let's check backend... relationships use UUIDs (id column), but agentium_id is the public ID.
    // Wait, the frontend `Agent` type has `subordinates: string[]`. 
    // Is that list of UUIDs or AgentiumIDs?
    // In `agents.py` `to_dict`: `'subordinates': [sub.agentium_id for sub in self.subordinates]`.
    // It uses AgentiumIDs. 
    // So mapping by AgentiumID is correct.

    const headOfCouncil = agents.find(a => a.agent_type === 'head_of_council');

    return (
        <div className="p-6 h-full flex flex-col">
            <div className="flex justify-between items-center mb-6">
                <div>
                    <h1 className="text-3xl font-bold text-white mb-2">Agent Hierarchy</h1>
                    <p className="text-gray-400">Manage your AI workforce</p>
                </div>

                <div className="flex bg-gray-800 rounded-lg p-1 border border-gray-700">
                    <button
                        onClick={() => setViewMode('tree')}
                        className={`p-2 rounded ${viewMode === 'tree' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        <LayoutGrid className="w-5 h-5" />
                    </button>
                    <button
                        onClick={() => setViewMode('list')}
                        className={`p-2 rounded ${viewMode === 'list' ? 'bg-gray-700 text-white' : 'text-gray-400 hover:text-white'}`}
                    >
                        <List className="w-5 h-5" />
                    </button>
                </div>
            </div>

            <div className="flex-1 overflow-auto bg-gray-900/50 rounded-xl border border-gray-800 p-6">
                {isLoading ? (
                    <div className="text-center text-gray-500 mt-10">Loading agents...</div>
                ) : agents.length === 0 ? (
                    <div className="text-center text-gray-500 mt-10">No agents found. System not initialized?</div>
                ) : viewMode === 'tree' ? (
                    headOfCouncil ? (
                        // We need to pass the FULL map to the tree so it can lookup any child by ID
                        <AgentTree
                            agent={headOfCouncil}
                            agentsMap={agentsMap}
                            onSpawn={setSpawnParent}
                            onTerminate={handleTerminate}
                        />
                    ) : (
                        <div className="text-red-400">Error: Head of Council not found in agent list.</div>
                    )
                ) : (
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {agents.map(agent => (
                            <div key={agent.id}> {/* Wrapper just for grid layout if needed */}
                                <div className="bg-gray-800 p-4 rounded border border-gray-700">
                                    <h3 className="text-white font-bold">{agent.name}</h3>
                                    <p className="text-sm text-gray-400">{agent.agent_type}</p>
                                    <div className="mt-2 text-xs text-gray-500">ID: {agent.agentium_id}</div>
                                </div>
                            </div>
                        ))}
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
