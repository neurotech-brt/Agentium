/**
 * VotingInterface Component - Real-time voting display for active amendments.
 * Can be embedded in MonitoringPage or used standalone.
 */

import React, { useState, useEffect } from 'react';
import {
    votingService,
    AmendmentVoting,
    VoteType,
    getTimeRemaining,
    calculateVotePercentage,
    isVotingActive,
    getStatusColor,
} from '../../services/voting';
import { Loader2, ThumbsUp, ThumbsDown, Minus, Clock, Users, CheckCircle, XCircle } from 'lucide-react';

interface VotingInterfaceProps {
    embedded?: boolean;
    onVoteCast?: (amendmentId: string) => void;
}

export const VotingInterface: React.FC<VotingInterfaceProps> = ({ embedded = false, onVoteCast }) => {
    const [amendments, setAmendments] = useState<AmendmentVoting[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedAmendment, setSelectedAmendment] = useState<AmendmentVoting | null>(null);
    const [castVote, setCastVote] = useState<VoteType | null>(null);
    const [rationale, setRationale] = useState('');
    const [isVoting, setIsVoting] = useState(false);

    useEffect(() => {
        loadAmendments();
        // Poll for updates every 30 seconds when voting is active
        const interval = setInterval(loadAmendments, 30000);
        return () => clearInterval(interval);
    }, []);

    const loadAmendments = async () => {
        try {
            const data = await votingService.getAmendmentVotings();
            setAmendments(data);
        } catch (error) {
            console.error('Failed to load amendments:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleVote = async (amendmentId: string) => {
        if (!castVote) return;
        setIsVoting(true);
        try {
            await votingService.castVote(amendmentId, castVote, rationale || undefined);
            setCastVote(null);
            setRationale('');
            setSelectedAmendment(null);
            await loadAmendments();
            onVoteCast?.(amendmentId);
        } catch (error: any) {
            alert(`Failed to cast vote: ${error.response?.data?.detail || error.message}`);
        } finally {
            setIsVoting(false);
        }
    };

    const activeAmendments = amendments.filter((a) => isVotingActive(a));
    const totalVotes = (a: AmendmentVoting) => a.votes_for + a.votes_against + a.votes_abstain;

    if (isLoading) {
        return (
            <div className="voting-interface loading flex items-center justify-center p-8">
                <Loader2 className="w-6 h-6 animate-spin text-blue-600 mr-2" />
                <span>Loading active votes...</span>
            </div>
        );
    }

    return (
        <div className={`voting-interface ${embedded ? 'embedded' : ''}`}>
            {!embedded && (
                <div className="interface-header mb-6">
                    <h2 className="text-xl font-semibold flex items-center gap-2">
                        <CheckCircle className="w-5 h-5 text-blue-600" />
                        Active Council Votes
                    </h2>
                    <p className="text-sm text-gray-500 dark:text-gray-400">
                        Real-time voting on constitutional amendments
                    </p>
                </div>
            )}

            {activeAmendments.length === 0 ? (
                <div className="empty-state text-center py-8 text-gray-500">
                    <CheckCircle className="w-12 h-12 mx-auto mb-3 text-gray-300 dark:text-gray-600" />
                    <p>No active votes at this time.</p>
                </div>
            ) : (
                <div className="amendments-list space-y-4">
                    {activeAmendments.map((amendment) => (
                        <div
                            key={amendment.id}
                            className={`amendment-card bg-white dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700 p-4 ${
                                selectedAmendment?.id === amendment.id ? 'ring-2 ring-blue-500' : ''
                            }`}
                            onClick={() => setSelectedAmendment(amendment)}
                        >
                            <div className="flex justify-between items-start mb-3">
                                <div>
                                    <h3 className="font-semibold text-gray-900 dark:text-white">
                                        {amendment.title || amendment.agentium_id}
                                    </h3>
                                    <div className="flex items-center gap-3 mt-1">
                                        <span
                                            className="status-badge text-xs px-2 py-0.5 rounded"
                                            style={{
                                                backgroundColor: `${getStatusColor(amendment.status)}20`,
                                                color: getStatusColor(amendment.status),
                                            }}
                                        >
                                            {amendment.status.toUpperCase()}
                                        </span>
                                        <span className="text-xs text-gray-500 flex items-center gap-1">
                                            <Users className="w-3 h-3" />
                                            {amendment.eligible_voters?.length || 0} eligible
                                        </span>
                                    </div>
                                </div>
                                <div className="text-right">
                                    <div className="flex items-center gap-1 text-sm text-orange-600">
                                        <Clock className="w-4 h-4" />
                                        {getTimeRemaining(amendment.ended_at)}
                                    </div>
                                </div>
                            </div>

                            {/* Vote Progress */}
                            <div className="vote-tally mb-3">
                                <div className="flex justify-between text-sm mb-1">
                                    <span className="text-green-600">
                                        FOR: {amendment.votes_for}
                                    </span>
                                    <span className="text-gray-500">
                                        {totalVotes(amendment)} / {amendment.eligible_voters?.length || 0} votes
                                    </span>
                                    <span className="text-red-600">
                                        AGAINST: {amendment.votes_against}
                                    </span>
                                </div>
                                <div className="flex h-2 rounded-full overflow-hidden bg-gray-200 dark:bg-gray-700">
                                    {totalVotes(amendment) > 0 && (
                                        <>
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
                                        </>
                                    )}
                                </div>
                            </div>

                            {/* Vote Actions */}
                            {selectedAmendment?.id === amendment.id && (
                                <div className="vote-actions mt-4 pt-4 border-t border-gray-200 dark:border-gray-700">
                                    <p className="text-sm font-medium mb-2">Cast your vote:</p>
                                    <div className="flex gap-2 mb-3">
                                        <button
                                            className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                                                castVote === 'for'
                                                    ? 'bg-green-600 text-white'
                                                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-green-100 dark:hover:bg-green-900'
                                            }`}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setCastVote('for');
                                            }}
                                        >
                                            <ThumbsUp className="w-4 h-4" />
                                            For
                                        </button>
                                        <button
                                            className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                                                castVote === 'against'
                                                    ? 'bg-red-600 text-white'
                                                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-red-100 dark:hover:bg-red-900'
                                            }`}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setCastVote('against');
                                            }}
                                        >
                                            <ThumbsDown className="w-4 h-4" />
                                            Against
                                        </button>
                                        <button
                                            className={`flex-1 py-2 px-4 rounded-lg flex items-center justify-center gap-2 transition-colors ${
                                                castVote === 'abstain'
                                                    ? 'bg-gray-600 text-white'
                                                    : 'bg-gray-100 dark:bg-gray-700 hover:bg-gray-200 dark:hover:bg-gray-600'
                                            }`}
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setCastVote('abstain');
                                            }}
                                        >
                                            <Minus className="w-4 h-4" />
                                            Abstain
                                        </button>
                                    </div>

                                    {castVote && (
                                        <>
                                            <textarea
                                                className="w-full p-2 border border-gray-300 dark:border-gray-600 rounded-lg bg-white dark:bg-gray-900 text-sm mb-2"
                                                placeholder="Optional: Provide rationale for your vote..."
                                                value={rationale}
                                                onChange={(e) => setRationale(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                                rows={2}
                                            />
                                            <button
                                                className="w-full py-2 px-4 bg-blue-600 hover:bg-blue-700 text-white rounded-lg font-medium transition-colors disabled:opacity-50"
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleVote(amendment.id);
                                                }}
                                                disabled={isVoting}
                                            >
                                                {isVoting ? 'Submitting...' : 'Submit Vote'}
                                            </button>
                                        </>
                                    )}
                                </div>
                            )}
                        </div>
                    ))}
                </div>
            )}
        </div>
    );
};

export default VotingInterface;
