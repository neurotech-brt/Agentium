import React, { useState } from 'react';
import { Agent } from '../../types';
import { AgentCard } from './AgentCard';
import { ChevronRight, ChevronDown } from 'lucide-react';

interface AgentTreeProps {
    agent: Agent;
    agentsMap: Map<string, Agent>; // Map of ID -> Agent for O(1) lookups
    onSpawn: (agent: Agent) => void;
    onTerminate: (agent: Agent) => void;
    level?: number;
}

export const AgentTree: React.FC<AgentTreeProps> = ({ agent, agentsMap, onSpawn, onTerminate, level = 0 }) => {
    const [isExpanded, setIsExpanded] = useState(true);

    // Find children in the map based on IDs
    const children = agent.subordinates
        .map(id => agentsMap.get(id))
        .filter((a): a is Agent => a !== undefined);

    const hasChildren = children.length > 0;

    return (
        <div className="relative">
            {/* Connector line for tree structure */}
            {level > 0 && (
                <div
                    className="absolute border-l-2 border-gray-700 -left-6 top-0 h-full"
                    style={{ left: '-24px', height: '100%' }}
                />
            )}

            <div className="flex items-start gap-2 mb-4 relative">
                {level > 0 && (
                    <div
                        className="absolute w-6 border-t-2 border-gray-700"
                        style={{ left: '-24px', top: '24px' }}
                    />
                )}

                {hasChildren && (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="mt-3 p-1 rounded hover:bg-gray-700 text-gray-400"
                    >
                        {isExpanded ? <ChevronDown className="w-4 h-4" /> : <ChevronRight className="w-4 h-4" />}
                    </button>
                )}
                {!hasChildren && <div className="w-6" />} {/* Spacer */}

                <AgentCard agent={agent} onSpawn={onSpawn} onTerminate={onTerminate} />
            </div>

            {/* Recursively render children */}
            {isExpanded && hasChildren && (
                <div className="ml-12 border-l-2 border-gray-700 pl-6 space-y-4">
                    {/* We remove the margin/border here as it's handled by logical pseudo-elements in CSS usually, 
                     but for simplicity in React we can just indent. 
                     The connector lines above are a quick fix. Clean tree UI is hard.
                     Let's just do simple indentation for now. */}
                    <div className="border-l border-gray-700/50 -ml-6 pl-6 pt-2">
                        {children.map(child => (
                            <AgentTree
                                key={child.id}
                                agent={child}
                                agentsMap={agentsMap}
                                onSpawn={onSpawn}
                                onTerminate={onTerminate}
                                level={level + 1}
                            />
                        ))}
                    </div>
                </div>
            )}
        </div>
    );
};
