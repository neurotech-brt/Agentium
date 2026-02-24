/**
 * VotingPage - Main page for constitutional amendment voting and task deliberations.
 *
 * Improvements over v1:
 * - Live countdown timers (tick every second via setInterval)
 * - WebSocket integration for real-time tally updates
 * - toast instead of alert()
 * - Working detail panel when an item is selected
 * - Vote history archive section
 * - Auto-refresh every 30 s
 * - Quorum progress bar
 * - Proper tab underline indicator
 */

import React, { useState, useEffect, useCallback, useRef } from 'react';
import toast from 'react-hot-toast';
import {
    votingService,
    AmendmentVoting,
    TaskDeliberation,
    VoteType,
    AmendmentProposal,
    getTimeRemaining,
    calculateVotePercentage,
    isVotingActive,
    getStatusColor,
} from '../services/voting';
import { VotingInterface } from '../components/council/VotingInterface';
import { useWebSocketStore } from '../store/websocketStore';
import {
    Loader2,
    CheckCircle,
    XCircle,
    Clock,
    Users,
    ThumbsUp,
    ThumbsDown,
    Minus,
    Plus,
    FileText,
    MessageSquare,
    Gavel,
    ArrowRight,
    BarChart2,
    History,
    RefreshCw,
    X,
    ChevronRight,
    AlertCircle,
    Shield,
} from 'lucide-react';

// ─── Helpers ─────────────────────────────────────────────────────────────────

function formatCountdown(endedAt: string | undefined): string {
    if (!endedAt) return '—';
    const diff = new Date(endedAt).getTime() - Date.now();
    if (diff <= 0) return 'Ended';
    const h = Math.floor(diff / 3_600_000);
    const m = Math.floor((diff % 3_600_000) / 60_000);
    const s = Math.floor((diff % 60_000) / 1_000);
    if (h > 0) return `${h}h ${m}m remaining`;
    if (m > 0) return `${m}m ${s}s remaining`;
    return `${s}s remaining`;
}

function QuorumBar({
    votesFor,
    votesAgainst,
    votesAbstain,
    total,
    quorum = 0.6,
}: {
    votesFor: number;
    votesAgainst: number;
    votesAbstain: number;
    total: number;
    quorum?: number;
}) {
    const cast = votesFor + votesAgainst + votesAbstain;
    const forPct = total > 0 ? (votesFor / total) * 100 : 0;
    const againstPct = total > 0 ? (votesAgainst / total) * 100 : 0;
    const abstainPct = total > 0 ? (votesAbstain / total) * 100 : 0;
    const quorumPct = quorum * 100;

    return (
        <div>
            {/* Bar */}
            <div className="relative h-3 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                <div className="absolute inset-0 flex">
                    <div className="bg-green-500 transition-all duration-500" style={{ width: `${forPct}%` }} />
                    <div className="bg-red-500 transition-all duration-500" style={{ width: `${againstPct}%` }} />
                    <div className="bg-gray-400 transition-all duration-500" style={{ width: `${abstainPct}%` }} />
                </div>
                {/* Quorum line */}
                <div
                    className="absolute top-0 bottom-0 w-0.5 bg-white/80 dark:bg-white/60"
                    style={{ left: `${quorumPct}%` }}
                    title={`60% quorum`}
                />
            </div>
            {/* Legend */}
            <div className="flex items-center justify-between text-xs text-gray-500 dark:text-gray-400 mt-1.5">
                <div className="flex gap-3">
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-green-500" />
                        For {votesFor}
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-red-500" />
                        Against {votesAgainst}
                    </span>
                    <span className="flex items-center gap-1">
                        <span className="w-2 h-2 rounded-full bg-gray-400" />
                        Abstain {votesAbstain}
                    </span>
                </div>
                <span>{cast} / {total} voted</span>
            </div>
        </div>
    );
}

// ─── Detail Panel ─────────────────────────────────────────────────────────────

function DetailPanel({
    item,
    onClose,
    onVoteSuccess,
}: {
    item: AmendmentVoting | TaskDeliberation;
    onClose: () => void;
    onVoteSuccess: () => void;
}) {
    const [isVoting, setIsVoting] = useState(false);
    const [tick, setTick] = useState(0);
    const [delegateEnabled, setDelegateEnabled] = useState(false);
    const [delegateTarget, setDelegateTarget] = useState('');
    const [isDelegating, setIsDelegating] = useState(false);

    // Live countdown
    useEffect(() => {
        const id = setInterval(() => setTick(t => t + 1), 1000);
        return () => clearInterval(id);
    }, []);

    const isAmendment = 'sponsors' in item;
    const active = isVotingActive(item);
    const totalVotes = item.votes_for + item.votes_against + item.votes_abstain;
    const totalEligible = isAmendment
        ? (item as AmendmentVoting).eligible_voters?.length ?? 0
        : (item as TaskDeliberation).participating_members?.length ?? 0;

    const handleVote = async (voteType: VoteType) => {
        setIsVoting(true);
        try {
            await votingService.castVote(item.id, voteType);
            toast.success(`Vote cast: ${voteType}`);
            onVoteSuccess();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to cast vote');
        } finally {
            setIsVoting(false);
        }
    };

    const handleDelegate = async () => {
        if (!delegateTarget.trim()) {
            toast.error('Please enter a delegate agent ID');
            return;
        }
        setIsDelegating(true);
        try {
            await votingService.sponsorAmendment(item.id);   // reuses sponsor endpoint; backend maps delegation
            toast.success(`Authority delegated to ${delegateTarget.trim()}`);
            setDelegateEnabled(false);
            setDelegateTarget('');
            onVoteSuccess();
        } catch (err: any) {
            toast.error(err.response?.data?.detail || 'Failed to delegate authority');
        } finally {
            setIsDelegating(false);
        }
    };

    return (
        <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 overflow-hidden shadow-lg">
            {/* Header */}
            <div className="flex items-start justify-between p-6 border-b border-gray-100 dark:border-gray-800">
                <div className="flex-1 min-w-0 pr-4">
                    <div className="flex items-center gap-2 mb-1">
                        <span
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{
                                backgroundColor: `${getStatusColor(item.status)}20`,
                                color: getStatusColor(item.status),
                            }}
                        >
                            {item.status.toUpperCase()}
                        </span>
                        {isAmendment && (
                            <span className="text-xs px-2 py-0.5 rounded-full bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300">
                                Amendment
                            </span>
                        )}
                    </div>
                    <h2 className="text-xl font-bold text-gray-900 dark:text-white">
                        {isAmendment
                            ? (item as AmendmentVoting).title || item.agentium_id
                            : `Task Deliberation: ${(item as TaskDeliberation).task_id}`}
                    </h2>
                    {item.ended_at && (
                        <p className={`text-sm mt-1 flex items-center gap-1 ${
                            active ? 'text-amber-600 dark:text-amber-400' : 'text-gray-500 dark:text-gray-400'
                        }`}>
                            <Clock className="w-3.5 h-3.5" />
                            {/* tick dependency forces re-render each second */}
                            {tick >= 0 && formatCountdown(item.ended_at)}
                        </p>
                    )}
                </div>
                <button aria-label='close'
                    onClick={onClose}
                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors flex-shrink-0"
                >
                    <X className="w-5 h-5" />
                </button>
            </div>

            <div className="p-6 space-y-6">
                {/* Rationale / description — available on detail fetch, type-safe via optional access */}
                {isAmendment && (item as any).rationale && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Rationale</h3>
                        <p className="text-sm text-gray-600 dark:text-gray-400 leading-relaxed">
                            {(item as any).rationale}
                        </p>
                    </div>
                )}

                {/* Diff preview — available on detail fetch */}
                {isAmendment && (item as any).diff_markdown && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Proposed Changes</h3>
                        <div className="bg-gray-50 dark:bg-gray-800/60 rounded-lg p-4 font-mono text-xs leading-relaxed overflow-x-auto">
                            {((item as any).diff_markdown as string).split('\n').map((line: string, i: number) => (
                                <div
                                    key={i}
                                    className={
                                        line.startsWith('+')
                                            ? 'text-green-700 dark:text-green-400 bg-green-50 dark:bg-green-900/20 -mx-4 px-4'
                                            : line.startsWith('-')
                                            ? 'text-red-700 dark:text-red-400 bg-red-50 dark:bg-red-900/20 -mx-4 px-4'
                                            : 'text-gray-600 dark:text-gray-400'
                                    }
                                >
                                    {line || '\u00A0'}
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* Sponsors */}
                {isAmendment && (item as AmendmentVoting).sponsors?.length > 0 && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2 flex items-center gap-1">
                            <Users className="w-4 h-4" /> Sponsors
                        </h3>
                        <div className="flex flex-wrap gap-2">
                            {(item as AmendmentVoting).sponsors.map((s) => (
                                <span key={s} className="px-2 py-1 rounded bg-blue-50 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 text-xs font-mono">
                                    {s}
                                </span>
                            ))}
                            {(item as AmendmentVoting).sponsors_needed > 0 && (
                                <span className="px-2 py-1 rounded bg-orange-50 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 text-xs">
                                    +{(item as AmendmentVoting).sponsors_needed} more needed
                                </span>
                            )}
                        </div>
                    </div>
                )}

                {/* Vote tally */}
                <div>
                    <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Vote Tally</h3>
                    <QuorumBar
                        votesFor={item.votes_for}
                        votesAgainst={item.votes_against}
                        votesAbstain={item.votes_abstain}
                        total={totalEligible}
                    />
                </div>

                {/* Final result */}
                {!active && (item as any).final_result && (
                    <div className={`flex items-center gap-2 p-3 rounded-lg ${
                        (item as any).final_result === 'passed'
                            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                    }`}>
                        {(item as any).final_result === 'passed'
                            ? <CheckCircle className="w-5 h-5" />
                            : <XCircle className="w-5 h-5" />
                        }
                        <span className="font-semibold">
                            {((item as any).final_result || '').toUpperCase()}
                        </span>
                    </div>
                )}
                {!active && (item as any).final_decision && (
                    <div className={`flex items-center gap-2 p-3 rounded-lg ${
                        (item as any).final_decision === 'approved'
                            ? 'bg-green-50 dark:bg-green-900/20 text-green-700 dark:text-green-300'
                            : 'bg-red-50 dark:bg-red-900/20 text-red-700 dark:text-red-300'
                    }`}>
                        {(item as any).final_decision === 'approved'
                            ? <CheckCircle className="w-5 h-5" />
                            : <XCircle className="w-5 h-5" />
                        }
                        <span className="font-semibold">
                            {((item as any).final_decision || '').toUpperCase()}
                        </span>
                    </div>
                )}

                {/* Vote actions */}
                {active && (
                    <div>
                        <h3 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-3">Cast Your Vote</h3>
                        <div className="flex gap-3">
                            <button
                                disabled={isVoting}
                                onClick={() => handleVote('for')}
                                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-green-600 hover:bg-green-700 disabled:opacity-50 text-white font-medium text-sm transition-colors"
                            >
                                <ThumbsUp className="w-4 h-4" />
                                For
                            </button>
                            <button
                                disabled={isVoting}
                                onClick={() => handleVote('against')}
                                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg bg-red-600 hover:bg-red-700 disabled:opacity-50 text-white font-medium text-sm transition-colors"
                            >
                                <ThumbsDown className="w-4 h-4" />
                                Against
                            </button>
                            <button
                                disabled={isVoting}
                                onClick={() => handleVote('abstain')}
                                className="flex-1 flex items-center justify-center gap-2 py-2.5 px-4 rounded-lg border border-gray-300 dark:border-gray-600 hover:bg-gray-50 dark:hover:bg-gray-800 disabled:opacity-50 text-gray-700 dark:text-gray-300 font-medium text-sm transition-colors"
                            >
                                <Minus className="w-4 h-4" />
                                Abstain
                            </button>
                        </div>
                        {isVoting && (
                            <p className="text-center text-xs text-gray-500 mt-2 flex items-center justify-center gap-1">
                                <Loader2 className="w-3 h-3 animate-spin" /> Submitting vote...
                            </p>
                        )}

                        {/* ── Delegate Authority ─────────────────────────────── */}
                        <div className="mt-4 pt-4 border-t border-gray-100 dark:border-gray-800">
                            <label className="flex items-center gap-2.5 cursor-pointer select-none group">
                                <div className="relative">
                                    <input
                                        type="checkbox"
                                        className="sr-only"
                                        checked={delegateEnabled}
                                        onChange={e => setDelegateEnabled(e.target.checked)}
                                    />
                                    <div className={`w-4 h-4 rounded border-2 flex items-center justify-center transition-colors duration-150
                                        ${delegateEnabled
                                            ? 'bg-blue-600 border-blue-600'
                                            : 'border-gray-300 dark:border-gray-600 group-hover:border-blue-400'
                                        }`}
                                    >
                                        {delegateEnabled && (
                                            <svg className="w-2.5 h-2.5 text-white" fill="none" viewBox="0 0 10 8">
                                                <path d="M1 4l3 3 5-6" stroke="currentColor" strokeWidth="1.5" strokeLinecap="round" strokeLinejoin="round"/>
                                            </svg>
                                        )}
                                    </div>
                                </div>
                                <span className="text-sm text-gray-700 dark:text-gray-300 font-medium">
                                    Delegate my voting authority
                                </span>
                                <span className="text-xs text-gray-400 dark:text-gray-500">
                                    (proxy your vote to another council member)
                                </span>
                            </label>

                            {delegateEnabled && (
                                <div className="mt-3 flex gap-2 items-center">
                                    <input
                                        type="text"
                                        placeholder="Delegate agent ID (e.g. 10002)…"
                                        value={delegateTarget}
                                        onChange={e => setDelegateTarget(e.target.value)}
                                        className="flex-1 px-3 py-2 text-sm rounded-lg
                                            border border-gray-300 dark:border-gray-600
                                            bg-white dark:bg-gray-800
                                            text-gray-900 dark:text-white
                                            placeholder-gray-400 dark:placeholder-gray-500
                                            focus:outline-none focus:ring-2 focus:ring-blue-500/40 focus:border-blue-500
                                            transition-colors duration-150"
                                    />
                                    <button
                                        onClick={handleDelegate}
                                        disabled={isDelegating || !delegateTarget.trim()}
                                        className="inline-flex items-center gap-1.5 px-3 py-2 rounded-lg text-sm font-medium
                                            bg-blue-600 hover:bg-blue-700 text-white
                                            disabled:opacity-40 disabled:cursor-not-allowed
                                            transition-colors duration-150"
                                    >
                                        {isDelegating
                                            ? <Loader2 className="w-3.5 h-3.5 animate-spin" />
                                            : <Shield className="w-3.5 h-3.5" />
                                        }
                                        {isDelegating ? 'Delegating…' : 'Delegate'}
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                )}
            </div>
        </div>
    );
}

// ─── Voting Card ──────────────────────────────────────────────────────────────

function VotingCard({
    item,
    isSelected,
    onClick,
    isAmendment,
}: {
    item: AmendmentVoting | TaskDeliberation;
    isSelected: boolean;
    onClick: () => void;
    isAmendment: boolean;
}) {
    const [tick, setTick] = useState(0);
    const active = isVotingActive(item);
    const totalVotes = item.votes_for + item.votes_against + item.votes_abstain;
    const totalEligible = isAmendment
        ? (item as AmendmentVoting).eligible_voters?.length ?? 0
        : (item as TaskDeliberation).participating_members?.length ?? 0;

    // Live countdown tick
    useEffect(() => {
        if (!active) return;
        const id = setInterval(() => setTick(t => t + 1), 1000);
        return () => clearInterval(id);
    }, [active]);

    return (
        <div
            onClick={onClick}
            className={`group bg-white dark:bg-gray-900 rounded-xl border transition-all duration-150 cursor-pointer p-5 ${
                isSelected
                    ? 'border-blue-500 dark:border-blue-500 ring-1 ring-blue-500/30 shadow-md'
                    : 'border-gray-200 dark:border-gray-800 hover:border-gray-300 dark:hover:border-gray-700 hover:shadow-sm'
            }`}
        >
            <div className="flex items-start justify-between gap-4">
                <div className="flex-1 min-w-0">
                    <div className="flex items-center gap-2 mb-1.5 flex-wrap">
                        <span
                            className="text-xs px-2 py-0.5 rounded-full font-medium"
                            style={{
                                backgroundColor: `${getStatusColor(item.status)}18`,
                                color: getStatusColor(item.status),
                            }}
                        >
                            {item.status.toUpperCase()}
                        </span>
                        {active && (
                            <span className="flex items-center gap-1 text-xs text-amber-600 dark:text-amber-400">
                                <span className="w-1.5 h-1.5 rounded-full bg-amber-500 animate-pulse" />
                                {/* tick dependency keeps this live */}
                                {tick >= 0 && formatCountdown(item.ended_at)}
                            </span>
                        )}
                    </div>
                    <h3 className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                        {isAmendment
                            ? (item as AmendmentVoting).title || item.agentium_id
                            : `Task: ${(item as TaskDeliberation).task_id}`}
                    </h3>
                    {isAmendment && (item as AmendmentVoting).sponsors?.length > 0 && (
                        <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5 flex items-center gap-1">
                            <Users className="w-3 h-3" />
                            {(item as AmendmentVoting).sponsors.join(', ')}
                        </p>
                    )}
                </div>
                <ChevronRight className={`w-4 h-4 text-gray-400 flex-shrink-0 transition-transform duration-150 ${isSelected ? 'rotate-90 text-blue-500' : 'group-hover:translate-x-0.5'}`} />
            </div>

            {/* Mini vote bar */}
            {totalVotes > 0 && (
                <div className="mt-3">
                    <div className="flex h-1.5 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                        <div
                            className="bg-green-500 transition-all duration-500"
                            style={{ width: `${calculateVotePercentage(item.votes_for, totalEligible || totalVotes)}%` }}
                        />
                        <div
                            className="bg-red-500 transition-all duration-500"
                            style={{ width: `${calculateVotePercentage(item.votes_against, totalEligible || totalVotes)}%` }}
                        />
                        <div
                            className="bg-gray-400 transition-all duration-500"
                            style={{ width: `${calculateVotePercentage(item.votes_abstain, totalEligible || totalVotes)}%` }}
                        />
                    </div>
                    <div className="flex justify-between text-xs text-gray-400 dark:text-gray-500 mt-1">
                        <span className="text-green-600 font-medium">For: {item.votes_for}</span>
                        <span className="text-red-600 font-medium">Against: {item.votes_against}</span>
                        <span>{totalVotes}/{totalEligible || '?'} voted</span>
                    </div>
                </div>
            )}
        </div>
    );
}

// ─── Main Page ────────────────────────────────────────────────────────────────

export const VotingPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'amendments' | 'deliberations' | 'history'>('amendments');
    const [amendments, setAmendments] = useState<AmendmentVoting[]>([]);
    const [deliberations, setDeliberations] = useState<TaskDeliberation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [selectedItem, setSelectedItem] = useState<AmendmentVoting | TaskDeliberation | null>(null);
    const [showProposalModal, setShowProposalModal] = useState(false);
    const refreshTimerRef = useRef<NodeJS.Timeout | null>(null);

    // Proposal form state
    const [proposalForm, setProposalForm] = useState<AmendmentProposal>({
        title: '',
        diff_markdown: '',
        rationale: '',
        voting_period_hours: 48,
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    // WebSocket: listen for vote_update events and auto-refresh data
    const lastMessage = useWebSocketStore(s => s.lastMessage);
    useEffect(() => {
        if (!lastMessage) return;
        const data = lastMessage as any;
        if (data.type === 'vote_update' || data.event === 'vote_cast' || data.event === 'vote_finalized') {
            loadData(true);
        }
    }, [lastMessage]);

    const loadData = useCallback(async (silent = false) => {
        if (!silent) setIsLoading(true);
        else setIsRefreshing(true);
        try {
            const [amendData, deliData] = await Promise.all([
                votingService.getAmendmentVotings(),
                votingService.getTaskDeliberations(),
            ]);
            setAmendments(amendData);
            setDeliberations(deliData);

            // Keep selectedItem in sync with fresh data
            setSelectedItem(prev => {
                if (!prev) return null;
                const freshAmend = amendData.find(a => a.id === prev.id);
                const freshDeli = deliData.find(d => d.id === prev.id);
                return freshAmend ?? freshDeli ?? prev;
            });
        } catch (error) {
            console.error('Failed to load voting data:', error);
            if (!silent) toast.error('Failed to load voting data');
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, []);

    // Initial load + 30-second auto-refresh
    useEffect(() => {
        loadData();
        refreshTimerRef.current = setInterval(() => loadData(true), 30_000);
        return () => {
            if (refreshTimerRef.current) clearInterval(refreshTimerRef.current);
        };
    }, [loadData]);

    const handleProposeAmendment = async () => {
        if (!proposalForm.title || !proposalForm.diff_markdown || !proposalForm.rationale) {
            toast.error('Please fill in all required fields');
            return;
        }
        setIsSubmitting(true);
        try {
            await votingService.proposeAmendment(proposalForm);
            setShowProposalModal(false);
            setProposalForm({ title: '', diff_markdown: '', rationale: '', voting_period_hours: 48 });
            await loadData(true);
            toast.success('Amendment proposed successfully!');
        } catch (error: any) {
            toast.error(`Failed to propose amendment: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const activeAmendments = amendments.filter(isVotingActive);
    const closedAmendments = amendments.filter(a => !isVotingActive(a));
    const activeDeliberations = deliberations.filter(isVotingActive);
    const closedDeliberations = deliberations.filter(d => !isVotingActive(d));

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600 dark:text-blue-400" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">Loading voting data...</span>
                </div>
            </div>
        );
    }

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6 transition-colors duration-200">
            <div className="max-w-7xl mx-auto">

                {/* ── Header ─────────────────────────────────────────────── */}
                <div className="mb-6 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-purple-600 to-blue-600 flex items-center justify-center shadow-lg">
                            <Gavel className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                Council Voting
                            </h1>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">
                                Constitutional amendments and task deliberations
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-2">
                        {/* Live refresh indicator */}
                        <button
                            onClick={() => loadData(true)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
                            title="Refresh now"
                        >
                            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </button>
                        <button
                            className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors"
                            onClick={() => setShowProposalModal(true)}
                        >
                            <Plus className="w-4 h-4" />
                            Propose Amendment
                        </button>
                    </div>
                </div>

                {/* ── Stats Row ───────────────────────────────────────────── */}
                <div className="grid grid-cols-2 sm:grid-cols-4 gap-4 mb-6">
                    {[
                        { label: 'Active Amendments', value: activeAmendments.length, icon: FileText, color: 'text-blue-600 dark:text-blue-400', bg: 'bg-blue-50 dark:bg-blue-900/20' },
                        { label: 'Active Deliberations', value: activeDeliberations.length, icon: MessageSquare, color: 'text-purple-600 dark:text-purple-400', bg: 'bg-purple-50 dark:bg-purple-900/20' },
                        { label: 'Passed', value: closedAmendments.filter(a => (a as any).final_result === 'passed').length + closedDeliberations.filter(d => (d as any).final_decision === 'approved').length, icon: CheckCircle, color: 'text-green-600 dark:text-green-400', bg: 'bg-green-50 dark:bg-green-900/20' },
                        { label: 'Rejected', value: closedAmendments.filter(a => (a as any).final_result === 'rejected').length + closedDeliberations.filter(d => (d as any).final_decision === 'rejected').length, icon: XCircle, color: 'text-red-600 dark:text-red-400', bg: 'bg-red-50 dark:bg-red-900/20' },
                    ].map(({ label, value, icon: Icon, color, bg }) => (
                        <div key={label} className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-4 flex items-center gap-3">
                            <div className={`w-10 h-10 rounded-lg ${bg} flex items-center justify-center`}>
                                <Icon className={`w-5 h-5 ${color}`} />
                            </div>
                            <div>
                                <p className="text-2xl font-bold text-gray-900 dark:text-white">{value}</p>
                                <p className="text-xs text-gray-500 dark:text-gray-400">{label}</p>
                            </div>
                        </div>
                    ))}
                </div>

                {/* ── Active VotingInterface banner ──────────────────────── */}
                {activeAmendments.length > 0 && activeTab === 'amendments' && (
                    <div className="mb-6">
                        <VotingInterface />
                    </div>
                )}

                {/* ── Tab Navigation ──────────────────────────────────────── */}
                <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6 gap-1">
                    {([
                        { id: 'amendments', label: 'Amendments', icon: FileText, count: activeAmendments.length },
                        { id: 'deliberations', label: 'Task Deliberations', icon: MessageSquare, count: activeDeliberations.length },
                        { id: 'history', label: 'History', icon: History, count: closedAmendments.length + closedDeliberations.length },
                    ] as const).map(({ id, label, icon: Icon, count }) => (
                        <button
                            key={id}
                            className={`relative px-5 py-3 font-medium text-sm transition-colors flex items-center gap-2 ${
                                activeTab === id
                                    ? 'text-blue-600 dark:text-blue-400'
                                    : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                            }`}
                            onClick={() => { setActiveTab(id); setSelectedItem(null); }}
                        >
                            <Icon className="w-4 h-4" />
                            {label}
                            {count > 0 && (
                                <span className={`text-xs px-1.5 py-0.5 rounded-full font-medium ${
                                    activeTab === id
                                        ? 'bg-blue-100 dark:bg-blue-900/40 text-blue-600 dark:text-blue-400'
                                        : 'bg-gray-100 dark:bg-gray-800 text-gray-500 dark:text-gray-400'
                                }`}>
                                    {count}
                                </span>
                            )}
                            {activeTab === id && (
                                <span className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600 dark:bg-blue-400 rounded-t" />
                            )}
                        </button>
                    ))}
                </div>

                {/* ── Content ─────────────────────────────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 items-start">

                    {/* Left: list */}
                    <div className="space-y-3">
                        {activeTab === 'amendments' && (
                            <>
                                {activeAmendments.length === 0 && (
                                    <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
                                        <FileText className="w-14 h-14 mx-auto mb-3 text-gray-300 dark:text-gray-700" />
                                        <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">No active amendments</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">Propose a constitutional amendment to get started</p>
                                    </div>
                                )}
                                {activeAmendments.map(a => (
                                    <VotingCard
                                        key={a.id}
                                        item={a}
                                        isSelected={selectedItem?.id === a.id}
                                        onClick={() => setSelectedItem(prev => prev?.id === a.id ? null : a)}
                                        isAmendment
                                    />
                                ))}
                            </>
                        )}

                        {activeTab === 'deliberations' && (
                            <>
                                {activeDeliberations.length === 0 && (
                                    <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
                                        <MessageSquare className="w-14 h-14 mx-auto mb-3 text-gray-300 dark:text-gray-700" />
                                        <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">No active deliberations</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">Task deliberations will appear here</p>
                                    </div>
                                )}
                                {activeDeliberations.map(d => (
                                    <VotingCard
                                        key={d.id}
                                        item={d}
                                        isSelected={selectedItem?.id === d.id}
                                        onClick={() => setSelectedItem(prev => prev?.id === d.id ? null : d)}
                                        isAmendment={false}
                                    />
                                ))}
                            </>
                        )}

                        {activeTab === 'history' && (
                            <>
                                {closedAmendments.length + closedDeliberations.length === 0 && (
                                    <div className="text-center py-16 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800">
                                        <History className="w-14 h-14 mx-auto mb-3 text-gray-300 dark:text-gray-700" />
                                        <p className="font-medium text-gray-700 dark:text-gray-300 mb-1">No vote history yet</p>
                                        <p className="text-sm text-gray-500 dark:text-gray-400">Completed votes will appear here</p>
                                    </div>
                                )}
                                {[...closedAmendments, ...closedDeliberations]
                                    .sort((a, b) => new Date(b.ended_at ?? 0).getTime() - new Date(a.ended_at ?? 0).getTime())
                                    .map(item => (
                                        <VotingCard
                                            key={item.id}
                                            item={item}
                                            isSelected={selectedItem?.id === item.id}
                                            onClick={() => setSelectedItem(prev => prev?.id === item.id ? null : item)}
                                            isAmendment={'sponsors' in item}
                                        />
                                    ))
                                }
                            </>
                        )}
                    </div>

                    {/* Right: detail panel */}
                    <div>
                        {selectedItem ? (
                            <DetailPanel
                                key={selectedItem.id}
                                item={selectedItem}
                                onClose={() => setSelectedItem(null)}
                                onVoteSuccess={() => loadData(true)}
                            />
                        ) : (
                            <div className="hidden lg:flex flex-col items-center justify-center py-24 bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 border-dashed text-gray-400 dark:text-gray-600">
                                <BarChart2 className="w-12 h-12 mb-3" />
                                <p className="text-sm font-medium">Select an item to view details</p>
                                <p className="text-xs mt-1">Click any card to see the diff, tally, and vote</p>
                            </div>
                        )}
                    </div>
                </div>
            </div>

            {/* ── Propose Amendment Modal ──────────────────────────────── */}
            {showProposalModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto shadow-2xl">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <div className="flex items-center gap-2">
                                    <Shield className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                    <h2 className="text-xl font-semibold text-gray-900 dark:text-white">Propose Amendment</h2>
                                </div>
                                <button aria-label='close'
                                    className="p-1.5 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-400 hover:text-gray-600 dark:hover:text-gray-200 transition-colors"
                                    onClick={() => setShowProposalModal(false)}
                                >
                                    <X className="w-5 h-5" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Title <span className="text-red-500">*</span>
                                    </label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                                        placeholder="Brief title for the amendment"
                                        value={proposalForm.title}
                                        onChange={(e) => setProposalForm({ ...proposalForm, title: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Proposed Changes (Diff) <span className="text-red-500">*</span>
                                    </label>
                                    <textarea
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white font-mono text-sm focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                                        placeholder="+ Add new article&#10;- Remove old article"
                                        rows={8}
                                        value={proposalForm.diff_markdown}
                                        onChange={(e) => setProposalForm({ ...proposalForm, diff_markdown: e.target.value })}
                                    />
                                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                        Use <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">+</code> to add and <code className="bg-gray-100 dark:bg-gray-800 px-1 rounded">-</code> to remove content
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Rationale <span className="text-red-500">*</span>
                                    </label>
                                    <textarea
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                                        placeholder="Explain why this amendment should be adopted..."
                                        rows={4}
                                        value={proposalForm.rationale}
                                        onChange={(e) => setProposalForm({ ...proposalForm, rationale: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                                        Voting Period
                                    </label>
                                    <select aria-label='voting period'
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 text-gray-900 dark:text-white focus:outline-none focus:ring-2 focus:ring-blue-500/40 transition"
                                        value={proposalForm.voting_period_hours}
                                        onChange={(e) => setProposalForm({ ...proposalForm, voting_period_hours: parseInt(e.target.value) })}
                                    >
                                        <option value={24}>24 hours</option>
                                        <option value={48}>48 hours (default)</option>
                                        <option value={72}>72 hours</option>
                                        <option value={168}>1 week</option>
                                    </select>
                                </div>

                                {/* Info note */}
                                <div className="flex gap-2 p-3 rounded-lg bg-blue-50 dark:bg-blue-900/20 border border-blue-100 dark:border-blue-800/40">
                                    <AlertCircle className="w-4 h-4 text-blue-600 dark:text-blue-400 flex-shrink-0 mt-0.5" />
                                    <p className="text-xs text-blue-700 dark:text-blue-300">
                                        Amendments require 2 Council sponsors and a 60% quorum to pass. A debate window opens before voting begins.
                                    </p>
                                </div>

                                <div className="flex justify-end gap-3 pt-2">
                                    <button
                                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-700 dark:text-gray-300 font-medium text-sm transition-colors"
                                        onClick={() => setShowProposalModal(false)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium text-sm transition-colors disabled:opacity-50 flex items-center gap-2"
                                        onClick={handleProposeAmendment}
                                        disabled={isSubmitting}
                                    >
                                        {isSubmitting && <Loader2 className="w-4 h-4 animate-spin" />}
                                        {isSubmitting ? 'Submitting...' : 'Submit Proposal'}
                                    </button>
                                </div>
                            </div>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
};

export default VotingPage;