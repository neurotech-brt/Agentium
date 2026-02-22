/**
 * VotingPage - Main page for constitutional amendment voting and task deliberations.
 * Provides tabs for switching between amendment voting and council deliberations.
 */

import React, { useState, useEffect } from 'react';
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
} from 'lucide-react';

export const VotingPage: React.FC = () => {
    const [activeTab, setActiveTab] = useState<'amendments' | 'deliberations'>('amendments');
    const [amendments, setAmendments] = useState<AmendmentVoting[]>([]);
    const [deliberations, setDeliberations] = useState<TaskDeliberation[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedItem, setSelectedItem] = useState<AmendmentVoting | TaskDeliberation | null>(null);
    const [showProposalModal, setShowProposalModal] = useState(false);

    // Proposal form state
    const [proposalForm, setProposalForm] = useState<AmendmentProposal>({
        title: '',
        diff_markdown: '',
        rationale: '',
        voting_period_hours: 48,
    });
    const [isSubmitting, setIsSubmitting] = useState(false);

    useEffect(() => {
        loadData();
    }, [activeTab]);

    const loadData = async () => {
        setIsLoading(true);
        try {
            if (activeTab === 'amendments') {
                const data = await votingService.getAmendmentVotings();
                setAmendments(data);
            } else {
                const data = await votingService.getTaskDeliberations();
                setDeliberations(data);
            }
        } catch (error) {
            console.error('Failed to load data:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleProposeAmendment = async () => {
        if (!proposalForm.title || !proposalForm.diff_markdown || !proposalForm.rationale) {
            alert('Please fill in all required fields');
            return;
        }

        setIsSubmitting(true);
        try {
            await votingService.proposeAmendment(proposalForm);
            setShowProposalModal(false);
            setProposalForm({ title: '', diff_markdown: '', rationale: '', voting_period_hours: 48 });
            await loadData();
            alert('Amendment proposed successfully!');
        } catch (error: any) {
            alert(`Failed to propose amendment: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsSubmitting(false);
        }
    };

    const activeAmendments = amendments.filter((a) => isVotingActive(a));
    const activeDeliberations = deliberations.filter((d) => isVotingActive(d));
    const totalVotes = (item: AmendmentVoting | TaskDeliberation) =>
        item.votes_for + item.votes_against + item.votes_abstain;

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
                {/* Header */}
                <div className="mb-8">
                    <div className="flex items-center gap-3 mb-3">
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
                </div>

                {/* Active Voting Interface */}
                {activeTab === 'amendments' && activeAmendments.length > 0 && (
                    <div className="mb-8">
                        <VotingInterface />
                    </div>
                )}

                {/* Tab Navigation */}
                <div className="flex border-b border-gray-200 dark:border-gray-700 mb-6">
                    <button
                        className={`px-6 py-3 font-medium text-sm transition-colors relative ${
                            activeTab === 'amendments'
                                ? 'text-blue-600 dark:text-blue-400'
                                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                        onClick={() => setActiveTab('amendments')}
                    >
                        <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4" />
                            Amendments
                        </div>
                        {activeTab === 'amendments' && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
                        )}
                    </button>
                    <button
                        className={`px-6 py-3 font-medium text-sm transition-colors relative ${
                            activeTab === 'deliberations'
                                ? 'text-blue-600 dark:text-blue-400'
                                : 'text-gray-500 dark:text-gray-400 hover:text-gray-700 dark:hover:text-gray-300'
                        }`}
                        onClick={() => setActiveTab('deliberations')}
                    >
                        <div className="flex items-center gap-2">
                            <MessageSquare className="w-4 h-4" />
                            Task Deliberations
                        </div>
                        {activeTab === 'deliberations' && (
                            <div className="absolute bottom-0 left-0 right-0 h-0.5 bg-blue-600" />
                        )}
                    </button>
                </div>

                {/* Content */}
                {activeTab === 'amendments' ? (
                    <div className="amendments-content">
                        {/* Propose Button */}
                        <div className="flex justify-end mb-4">
                            <button
                                className="flex items-center gap-2 px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors"
                                onClick={() => setShowProposalModal(true)}
                            >
                                <Plus className="w-4 h-4" />
                                Propose Amendment
                            </button>
                        </div>

                        {/* Amendments List */}
                        {amendments.length === 0 ? (
                            <div className="text-center py-12 text-gray-500">
                                <FileText className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                                <p className="text-lg mb-2">No amendments yet</p>
                                <p className="text-sm">Propose a constitutional amendment to get started</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {amendments.map((amendment) => (
                                    <div
                                        key={amendment.id}
                                        className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 cursor-pointer hover:shadow-md transition-shadow ${
                                            selectedItem?.id === amendment.id ? 'ring-2 ring-blue-500' : ''
                                        }`}
                                        onClick={() => setSelectedItem(amendment)}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                                    {amendment.title || amendment.agentium_id}
                                                </h3>
                                                <div className="flex items-center gap-3 flex-wrap">
                                                    <span
                                                        className="text-xs px-2 py-1 rounded"
                                                        style={{
                                                            backgroundColor: `${getStatusColor(amendment.status)}20`,
                                                            color: getStatusColor(amendment.status),
                                                        }}
                                                    >
                                                        {amendment.status.toUpperCase()}
                                                    </span>
                                                    {amendment.sponsors.length > 0 && (
                                                        <span className="text-xs text-gray-500 flex items-center gap-1">
                                                            <Users className="w-3 h-3" />
                                                            Sponsors: {amendment.sponsors.join(', ')}
                                                        </span>
                                                    )}
                                                    {amendment.sponsors_needed > 0 && (
                                                        <span className="text-xs text-orange-600">
                                                            {amendment.sponsors_needed} more sponsors needed
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                {amendment.ended_at && (
                                                    <div className="flex items-center gap-1 text-sm text-gray-500 mb-2">
                                                        <Clock className="w-4 h-4" />
                                                        {getTimeRemaining(amendment.ended_at)}
                                                    </div>
                                                )}
                                                <div className="flex gap-4 text-sm">
                                                    <span className="text-green-600 font-medium">
                                                        FOR: {amendment.votes_for}
                                                    </span>
                                                    <span className="text-red-600 font-medium">
                                                        AGAINST: {amendment.votes_against}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Vote Progress */}
                                        {totalVotes(amendment) > 0 && (
                                            <div className="mt-4">
                                                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                                                    <div
                                                        className="bg-green-500"
                                                        style={{
                                                            width: `${calculateVotePercentage(amendment.votes_for, totalVotes(amendment))}%`,
                                                        }}
                                                    />
                                                    <div
                                                        className="bg-red-500"
                                                        style={{
                                                            width: `${calculateVotePercentage(amendment.votes_against, totalVotes(amendment))}%`,
                                                        }}
                                                    />
                                                    <div
                                                        className="bg-gray-400"
                                                        style={{
                                                            width: `${calculateVotePercentage(amendment.votes_abstain, totalVotes(amendment))}%`,
                                                        }}
                                                    />
                                                </div>
                                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                    <span>
                                                        {totalVotes(amendment)} / {amendment.eligible_voters?.length || 0} votes
                                                    </span>
                                                    {amendment.final_result && (
                                                        <span
                                                            className={
                                                                amendment.final_result === 'passed'
                                                                    ? 'text-green-600'
                                                                    : 'text-red-600'
                                                            }
                                                        >
                                                            {amendment.final_result.toUpperCase()}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                ) : (
                    <div className="deliberations-content">
                        {deliberations.length === 0 ? (
                            <div className="text-center py-12 text-gray-500">
                                <MessageSquare className="w-16 h-16 mx-auto mb-4 text-gray-300 dark:text-gray-600" />
                                <p className="text-lg mb-2">No deliberations yet</p>
                                <p className="text-sm">Task deliberations will appear here</p>
                            </div>
                        ) : (
                            <div className="space-y-4">
                                {deliberations.map((deliberation) => (
                                    <div
                                        key={deliberation.id}
                                        className={`bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 cursor-pointer hover:shadow-md transition-shadow ${
                                            selectedItem?.id === deliberation.id ? 'ring-2 ring-blue-500' : ''
                                        }`}
                                        onClick={() => setSelectedItem(deliberation)}
                                    >
                                        <div className="flex justify-between items-start">
                                            <div>
                                                <h3 className="text-lg font-semibold text-gray-900 dark:text-white mb-2">
                                                    Task: {deliberation.task_id}
                                                </h3>
                                                <div className="flex items-center gap-3 flex-wrap">
                                                    <span
                                                        className="text-xs px-2 py-1 rounded"
                                                        style={{
                                                            backgroundColor: `${getStatusColor(deliberation.status)}20`,
                                                            color: getStatusColor(deliberation.status),
                                                        }}
                                                    >
                                                        {deliberation.status.toUpperCase()}
                                                    </span>
                                                    {deliberation.head_overridden && (
                                                        <span className="text-xs px-2 py-1 rounded bg-purple-100 text-purple-700 dark:bg-purple-900 dark:text-purple-300">
                                                            Head Overridden
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                            <div className="text-right">
                                                {deliberation.ended_at && (
                                                    <div className="flex items-center gap-1 text-sm text-gray-500 mb-2">
                                                        <Clock className="w-4 h-4" />
                                                        {getTimeRemaining(deliberation.ended_at)}
                                                    </div>
                                                )}
                                                <div className="flex gap-4 text-sm">
                                                    <span className="text-green-600 font-medium">
                                                        FOR: {deliberation.votes_for}
                                                    </span>
                                                    <span className="text-red-600 font-medium">
                                                        AGAINST: {deliberation.votes_against}
                                                    </span>
                                                </div>
                                            </div>
                                        </div>

                                        {/* Vote Progress */}
                                        {totalVotes(deliberation) > 0 && (
                                            <div className="mt-4">
                                                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                                                    <div
                                                        className="bg-green-500"
                                                        style={{
                                                            width: `${calculateVotePercentage(deliberation.votes_for, totalVotes(deliberation))}%`,
                                                        }}
                                                    />
                                                    <div
                                                        className="bg-red-500"
                                                        style={{
                                                            width: `${calculateVotePercentage(deliberation.votes_against, totalVotes(deliberation))}%`,
                                                        }}
                                                    />
                                                    <div
                                                        className="bg-gray-400"
                                                        style={{
                                                            width: `${calculateVotePercentage(deliberation.votes_abstain, totalVotes(deliberation))}%`,
                                                        }}
                                                    />
                                                </div>
                                                <div className="flex justify-between text-xs text-gray-500 mt-1">
                                                    <span>
                                                        {totalVotes(deliberation)} / {deliberation.participating_members?.length || 0} votes
                                                    </span>
                                                    {deliberation.final_decision && (
                                                        <span
                                                            className={
                                                                deliberation.final_decision === 'approved'
                                                                    ? 'text-green-600'
                                                                    : 'text-red-600'
                                                            }
                                                        >
                                                            {deliberation.final_decision.toUpperCase()}
                                                        </span>
                                                    )}
                                                </div>
                                            </div>
                                        )}
                                    </div>
                                ))}
                            </div>
                        )}
                    </div>
                )}
            </div>

            {/* Propose Amendment Modal */}
            {showProposalModal && (
                <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4">
                    <div className="bg-white dark:bg-gray-900 rounded-xl max-w-2xl w-full max-h-[90vh] overflow-y-auto">
                        <div className="p-6">
                            <div className="flex justify-between items-center mb-6">
                                <h2 className="text-xl font-semibold">Propose Amendment</h2>
                                <button
                                    className="text-gray-500 hover:text-gray-700 dark:hover:text-gray-300"
                                    onClick={() => setShowProposalModal(false)}
                                >
                                    <XCircle className="w-6 h-6" />
                                </button>
                            </div>

                            <div className="space-y-4">
                                <div>
                                    <label className="block text-sm font-medium mb-1">Title *</label>
                                    <input
                                        type="text"
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                                        placeholder="Brief title for the amendment"
                                        value={proposalForm.title}
                                        onChange={(e) => setProposalForm({ ...proposalForm, title: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Proposed Changes (Diff) *</label>
                                    <textarea
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800 font-mono text-sm"
                                        placeholder="+ Add new article&#10;- Remove old article"
                                        rows={8}
                                        value={proposalForm.diff_markdown}
                                        onChange={(e) =>
                                            setProposalForm({ ...proposalForm, diff_markdown: e.target.value })
                                        }
                                    />
                                    <p className="text-xs text-gray-500 mt-1">
                                        Use + to add new content, - to remove content
                                    </p>
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Rationale *</label>
                                    <textarea
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                                        placeholder="Explain why this amendment should be adopted..."
                                        rows={4}
                                        value={proposalForm.rationale}
                                        onChange={(e) => setProposalForm({ ...proposalForm, rationale: e.target.value })}
                                    />
                                </div>

                                <div>
                                    <label className="block text-sm font-medium mb-1">Voting Period (hours)</label>
                                    <select
                                        className="w-full px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-800"
                                        value={proposalForm.voting_period_hours}
                                        onChange={(e) =>
                                            setProposalForm({
                                                ...proposalForm,
                                                voting_period_hours: parseInt(e.target.value),
                                            })
                                        }
                                    >
                                        <option value={24}>24 hours</option>
                                        <option value={48}>48 hours</option>
                                        <option value={72}>72 hours</option>
                                        <option value={168}>1 week</option>
                                    </select>
                                </div>

                                <div className="flex justify-end gap-3 pt-4">
                                    <button
                                        className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 transition-colors"
                                        onClick={() => setShowProposalModal(false)}
                                    >
                                        Cancel
                                    </button>
                                    <button
                                        className="px-4 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                        onClick={handleProposeAmendment}
                                        disabled={isSubmitting}
                                    >
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
