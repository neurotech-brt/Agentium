/**
 * AgentTree — Phase 7.2
 *
 * Changes vs original:
 *  - Critic agents (agentium_id starting with 4, 5, or 6 → 4xxxx/5xxxx/6xxxx)
 *    are separated from the main governance tree and rendered in a "Critic Branch"
 *    section below with its own collapsible header.
 *  - AgentCard now shows health score ring + active task count badge (see AgentCard.tsx).
 *  - Rest of the tree logic is unchanged.
 */

import React, { useState } from 'react';
import { Agent } from '../../types';
import { AgentCard } from './AgentCard';
import { ChevronRight, ChevronDown, ShieldAlert } from 'lucide-react';

// ─── Helpers ─────────────────────────────────────────────────────────────────

/** Returns true for critic-tier agents (4xxxx / 5xxxx / 6xxxx ID prefix). */
function isCriticAgent(agent: Agent): boolean {
    const id = agent.agentium_id ?? agent.id ?? '';
    // Critic IDs start with 4, 5, or 6
    return /^[456]/.test(String(id));
}

// ─── Props ────────────────────────────────────────────────────────────────────

interface AgentTreeProps {
    agent: Agent;
    agentsMap: Map<string, Agent>;
    onSpawn: (agent: Agent) => void;
    onTerminate: (agent: Agent) => void;
    level?: number;
    /** When true, critic agents are NOT filtered out of children (used for the critic sub-tree render). */
    includeCritics?: boolean;
}

// ─── Recursive tree node ──────────────────────────────────────────────────────

export const AgentTree: React.FC<AgentTreeProps> = ({
    agent,
    agentsMap,
    onSpawn,
    onTerminate,
    level = 0,
    includeCritics = false,
}) => {
    const [isExpanded, setIsExpanded] = useState(true);
    const [criticExpanded, setCriticExpanded] = useState(true);

    if (!agent) return null;

    const subordinateIds = Array.isArray(agent?.subordinates) ? agent.subordinates : [];
    const allChildren = subordinateIds
        .map(id => agentsMap.get(id))
        .filter((a): a is Agent => a !== undefined);

    // At the root level (level === 0 and includeCritics is false), split
    // critic agents into their own branch so they don't pollute the main tree.
    const isRoot = level === 0 && !includeCritics;

    const mainChildren = isRoot
        ? allChildren.filter(a => !isCriticAgent(a))
        : allChildren;

    // Gather ALL critic agents from the whole agentsMap for the critic branch
    // (they may not be subordinates of head_of_council directly).
    const criticAgents: Agent[] = isRoot
        ? [...agentsMap.values()].filter(isCriticAgent)
        : [];

    const hasMainChildren = mainChildren.length > 0;
    const hasCritics = criticAgents.length > 0;

    return (
        <div className="relative">
            {/* Vertical connector */}
            {level > 0 && (
                <div
                    className="absolute border-l-2 border-slate-400 dark:border-slate-500"
                    style={{ left: '-24px', height: '100%', top: 0 }}
                />
            )}

            <div className="flex items-start gap-2 mb-4 relative">
                {/* Horizontal connector */}
                {level > 0 && (
                    <div
                        className="absolute w-6 border-t-2 border-slate-400 dark:border-slate-500"
                        style={{ left: '-24px', top: '24px' }}
                    />
                )}

                {hasMainChildren ? (
                    <button
                        onClick={() => setIsExpanded(!isExpanded)}
                        className="mt-3 p-1 rounded-lg hover:bg-slate-200 dark:hover:bg-slate-700
                            text-slate-600 dark:text-slate-300 transition-colors duration-150 flex-shrink-0"
                    >
                        {isExpanded
                            ? <ChevronDown className="w-4 h-4" />
                            : <ChevronRight className="w-4 h-4" />
                        }
                    </button>
                ) : (
                    <div className="w-6 flex-shrink-0" />
                )}

                <AgentCard agent={agent} onSpawn={onSpawn} onTerminate={onTerminate} />
            </div>

            {/* Main children */}
            {isExpanded && hasMainChildren && (
                <div className="ml-12 pl-6 space-y-0 border-l-2 border-slate-400 dark:border-slate-500">
                    <div className="border-l border-slate-300 dark:border-slate-600 -ml-6 pl-6 pt-2">
                        {mainChildren.map(child => (
                            <AgentTree
                                key={child.id || child.agentium_id}
                                agent={child}
                                agentsMap={agentsMap}
                                onSpawn={onSpawn}
                                onTerminate={onTerminate}
                                level={level + 1}
                                includeCritics={false}
                            />
                        ))}
                    </div>
                </div>
            )}

            {/* ── Critic Branch (root only) ─────────────────────────────────── */}
            {isRoot && hasCritics && (
                <div className="mt-8">
                    {/* Section header */}
                    <button
                        onClick={() => setCriticExpanded(x => !x)}
                        className="flex items-center gap-2 mb-4 group"
                    >
                        <div className="flex items-center gap-2 px-3 py-1.5 rounded-lg
                            bg-rose-50 dark:bg-rose-500/10
                            border border-rose-200 dark:border-rose-500/20
                            text-rose-700 dark:text-rose-300
                            hover:bg-rose-100 dark:hover:bg-rose-500/20
                            transition-colors duration-150">
                            <ShieldAlert className="w-4 h-4" />
                            <span className="text-sm font-semibold">Critic Agents</span>
                            <span className="text-xs font-mono opacity-70">({criticAgents.length})</span>
                            {criticExpanded
                                ? <ChevronDown className="w-3.5 h-3.5" />
                                : <ChevronRight className="w-3.5 h-3.5" />
                            }
                        </div>
                        <div className="flex-1 h-px bg-rose-200 dark:bg-rose-500/20" />
                    </button>

                    {/* Critic cards grid */}
                    {criticExpanded && (
                        <div className="
                            relative rounded-xl border border-rose-200 dark:border-rose-500/20
                            bg-rose-50/40 dark:bg-rose-500/5 p-4
                        ">
                            {/* Subtle dot pattern */}
                            <div
                                className="absolute inset-0 rounded-xl
                                    bg-[radial-gradient(circle,_#fca5a5_1px,_transparent_1px)]
                                    dark:bg-[radial-gradient(circle,_#7f1d1d30_1px,_transparent_1px)]
                                    bg-[length:20px_20px] opacity-40 pointer-events-none"
                                aria-hidden="true"
                            />
                            <div className="relative z-10 flex flex-wrap gap-4">
                                {criticAgents.map(critic => (
                                    <div key={critic.id || critic.agentium_id} className="flex-shrink-0">
                                        <AgentCard
                                            agent={critic}
                                            onSpawn={onSpawn}
                                            onTerminate={onTerminate}
                                        />
                                    </div>
                                ))}
                            </div>
                        </div>
                    )}
                </div>
            )}
        </div>
    );
};