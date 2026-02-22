/**
 * CheckpointTimeline Component - Visual timeline of execution checkpoints.
 * Allows viewing, restoring, and branching from checkpoints.
 */

import React, { useState, useEffect } from 'react';
import { api } from '../../services/api';
import { CheckpointPhase } from '../../types';

// ============================================================================
// Types
// ============================================================================

export interface ExecutionCheckpoint {
    id: string;
    agentium_id: string;
    session_id: string;
    task_id: string;
    phase: CheckpointPhase;
    branch_name: string;
    parent_checkpoint_id?: string;
    agent_states: Record<string, any>;
    artifacts: Record<string, any>;
    task_state_snapshot: Record<string, any>;
    is_active: boolean;
    created_at: string;
    updated_at: string;
}

interface CheckpointTimelineProps {
    taskId?: string;
    sessionId?: string;
    onRestore?: (checkpointId: string) => void;
    onBranch?: (checkpointId: string, branchName: string) => void;
}

// ============================================================================
// Component
// ============================================================================

export const CheckpointTimeline: React.FC<CheckpointTimelineProps> = ({
    taskId,
    sessionId,
    onRestore,
    onBranch,
}) => {
    const [checkpoints, setCheckpoints] = useState<ExecutionCheckpoint[]>([]);
    const [isLoading, setIsLoading] = useState(true);
    const [selectedCheckpoint, setSelectedCheckpoint] = useState<ExecutionCheckpoint | null>(null);
    const [showDiff, setShowDiff] = useState(false);
    const [branchName, setBranchName] = useState('');

    useEffect(() => {
        loadCheckpoints();
    }, [taskId, sessionId]);

    const loadCheckpoints = async () => {
        setIsLoading(true);
        try {
            const params = new URLSearchParams();
            if (taskId) params.append('task_id', taskId);
            if (sessionId) params.append('session_id', sessionId);
            const query = params.toString() ? `?${params.toString()}` : '';

            const response = await api.get<ExecutionCheckpoint[]>(`/api/v1/checkpoints${query}`);
            setCheckpoints(response.data || []);
        } catch (error) {
            console.error('Failed to load checkpoints:', error);
        } finally {
            setIsLoading(false);
        }
    };

    const handleRestore = async (checkpointId: string) => {
        try {
            await api.post(`/api/v1/checkpoints/${checkpointId}/resume`);
            onRestore?.(checkpointId);
            alert('Task restored successfully!');
        } catch (error: any) {
            alert(`Failed to restore: ${error.response?.data?.detail || error.message}`);
        }
    };

    const handleBranch = async (checkpointId: string) => {
        if (!branchName.trim()) {
            alert('Please enter a branch name');
            return;
        }
        try {
            await api.post(`/api/v1/checkpoints/${checkpointId}/branch`, {
                branch_name: branchName,
            });
            onBranch?.(checkpointId, branchName);
            setBranchName('');
            setSelectedCheckpoint(null);
            alert(`Branch "${branchName}" created successfully!`);
        } catch (error: any) {
            alert(`Failed to create branch: ${error.response?.data?.detail || error.message}`);
        }
    };

    const getPhaseColor = (phase: string): string => {
        switch (phase) {
            case 'plan_approved':
                return '#3b82f6'; // blue
            case 'execution_complete':
                return '#f59e0b'; // amber
            case 'critique_passed':
                return '#10b981'; // green
            case 'manual':
                return '#8b5cf6'; // purple
            default:
                return '#6b7280'; // gray
        }
    };

    const getPhaseLabel = (phase: string): string => {
        switch (phase) {
            case 'plan_approved':
                return 'Plan Approved';
            case 'execution_complete':
                return 'Execution Complete';
            case 'critique_passed':
                return 'Critique Passed';
            case 'manual':
                return 'Manual Checkpoint';
            default:
                return phase;
        }
    };

    const formatDate = (dateStr: string): string => {
        const date = new Date(dateStr);
        return date.toLocaleString();
    };

    if (isLoading) {
        return (
            <div className="checkpoint-timeline loading">
                <div className="spinner" />
                <p>Loading checkpoints...</p>
            </div>
        );
    }

    if (checkpoints.length === 0) {
        return (
            <div className="checkpoint-timeline empty">
                <p>No checkpoints available for this task.</p>
            </div>
        );
    }

    return (
        <div className="checkpoint-timeline">
            <div className="timeline-header">
                <h3>Execution Timeline</h3>
                <button onClick={loadCheckpoints} className="refresh-btn">
                    Refresh
                </button>
            </div>

            <div className="timeline-container">
                {checkpoints.map((checkpoint, index) => (
                    <div
                        key={checkpoint.id}
                        className={`timeline-item ${selectedCheckpoint?.id === checkpoint.id ? 'selected' : ''}`}
                        onClick={() => setSelectedCheckpoint(checkpoint)}
                    >
                        <div className="timeline-marker">
                            <div
                                className="marker-dot"
                                style={{ backgroundColor: getPhaseColor(checkpoint.phase) }}
                            />
                            {index < checkpoints.length - 1 && <div className="marker-line" />}
                        </div>

                        <div className="timeline-content">
                            <div className="checkpoint-header">
                                <span
                                    className="phase-badge"
                                    style={{ backgroundColor: getPhaseColor(checkpoint.phase) }}
                                >
                                    {getPhaseLabel(checkpoint.phase)}
                                </span>
                                <span className="branch-name">{checkpoint.branch_name || 'main'}</span>
                            </div>

                            <div className="checkpoint-meta">
                                <span className="checkpoint-id" title={checkpoint.id}>
                                    {checkpoint.agentium_id}
                                </span>
                                <span className="checkpoint-date">{formatDate(checkpoint.created_at)}</span>
                            </div>

                            {selectedCheckpoint?.id === checkpoint.id && (
                                <div className="checkpoint-details">
                                    <div className="detail-section">
                                        <h4>Task State</h4>
                                        <pre className="state-preview">
                                            {JSON.stringify(checkpoint.task_state_snapshot, null, 2)}
                                        </pre>
                                    </div>

                                    <div className="detail-actions">
                                        <button
                                            className="restore-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                handleRestore(checkpoint.id);
                                            }}
                                        >
                                            Restore
                                        </button>
                                        <button
                                            className="branch-btn"
                                            onClick={(e) => {
                                                e.stopPropagation();
                                                setShowDiff(!showDiff);
                                            }}
                                        >
                                            {showDiff ? 'Hide Branch' : 'Branch'}
                                        </button>
                                    </div>

                                    {showDiff && (
                                        <div className="branch-form">
                                            <input
                                                type="text"
                                                placeholder="Enter branch name..."
                                                value={branchName}
                                                onChange={(e) => setBranchName(e.target.value)}
                                                onClick={(e) => e.stopPropagation()}
                                            />
                                            <button
                                                onClick={(e) => {
                                                    e.stopPropagation();
                                                    handleBranch(checkpoint.id);
                                                }}
                                            >
                                                Create Branch
                                            </button>
                                        </div>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                ))}
            </div>
        </div>
    );
};

export default CheckpointTimeline;
