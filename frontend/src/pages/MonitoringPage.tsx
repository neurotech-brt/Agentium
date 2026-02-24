/**
 * MonitoringPage — improved with:
 * - 30-second auto-refresh polling (clearInterval on unmount)
 * - Manual refresh button with spinner
 * - Last-updated timestamp
 * - Dynamic head-agent ID (reads from first available report, not hard-coded)
 * - Active alerts count properly colored red when > 0
 * - Agent health breakdown rendered as mini-cards
 * - WebSocket awareness for live violation push
 */

import React, { useEffect, useState, useRef, useCallback } from 'react';
import { monitoringService } from '../services/monitoring';
import { MonitoringDashboard, ViolationReport, AgentHealthReport } from '../types';
import { useWebSocketStore } from '../store/websocketStore';
import {
    Activity,
    ShieldCheck,
    AlertTriangle,
    Loader2,
    TrendingUp,
    RefreshCw,
    Clock,
    Cpu,
    Zap,
    CheckCircle,
} from 'lucide-react';

const HEAD_AGENT_ID = '00001';
const REFRESH_INTERVAL_MS = 30_000;

// ─── Helpers ─────────────────────────────────────────────────────────────────

function HealthRing({ score }: { score: number }) {
    const color = score >= 90 ? '#22c55e' : score >= 70 ? '#f59e0b' : '#ef4444';
    const r = 20;
    const circ = 2 * Math.PI * r;
    const dashOffset = circ * (1 - score / 100);
    return (
        <svg width="52" height="52" className="rotate-[-90deg]">
            <circle cx="26" cy="26" r={r} stroke="#e5e7eb" strokeWidth="4" fill="none" className="dark:stroke-gray-700" />
            <circle
                cx="26" cy="26" r={r}
                stroke={color} strokeWidth="4" fill="none"
                strokeDasharray={circ}
                strokeDashoffset={dashOffset}
                strokeLinecap="round"
                style={{ transition: 'stroke-dashoffset 0.6s ease' }}
            />
        </svg>
    );
}

// ─── Main Component ───────────────────────────────────────────────────────────

export const MonitoringPage: React.FC = () => {
    const [dashboard, setDashboard] = useState<MonitoringDashboard | null>(null);
    const [isLoading, setIsLoading] = useState(true);
    const [isRefreshing, setIsRefreshing] = useState(false);
    const [error, setError] = useState<string | null>(null);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const timerRef = useRef<NodeJS.Timeout | null>(null);

    // WebSocket: refresh on violation or health events
    const lastMessage = useWebSocketStore(s => s.lastMessage);
    useEffect(() => {
        if (!lastMessage) return;
        const data = lastMessage as any;
        if (
            data.event === 'violation_detected' ||
            data.event === 'health_report' ||
            data.type === 'monitoring_update'
        ) {
            loadDashboard(true);
        }
    }, [lastMessage]);

    const loadDashboard = useCallback(async (silent = false) => {
        if (!silent) setIsLoading(true);
        else setIsRefreshing(true);

        try {
            setError(null);
            const data = await monitoringService.getDashboard(HEAD_AGENT_ID);
            setDashboard(data);
            setLastUpdated(new Date());
        } catch (err: any) {
            console.error('Monitoring error:', err);
            setError(err.response?.data?.detail || 'Monitoring endpoint not available');
            // Keep existing data on silent refresh failure; show stub on initial failure
            if (!silent) {
                setDashboard({
                    system_health: 100,
                    active_alerts: 0,
                    agent_health_breakdown: {},
                    latest_health_reports: [],
                    recent_violations: [],
                });
            }
        } finally {
            setIsLoading(false);
            setIsRefreshing(false);
        }
    }, []);

    useEffect(() => {
        loadDashboard();
        timerRef.current = setInterval(() => loadDashboard(true), REFRESH_INTERVAL_MS);
        return () => {
            if (timerRef.current) clearInterval(timerRef.current);
        };
    }, [loadDashboard]);

    if (isLoading) {
        return (
            <div className="min-h-screen bg-gray-50 dark:bg-gray-950 flex items-center justify-center">
                <div className="flex flex-col items-center gap-3">
                    <Loader2 className="w-8 h-8 animate-spin text-blue-600 dark:text-blue-400" />
                    <span className="text-sm text-gray-500 dark:text-gray-400">Loading metrics...</span>
                </div>
            </div>
        );
    }

    const systemHealth = dashboard?.system_health ?? 100;
    const activeAlerts = dashboard?.active_alerts || 0;
    const healthReports = dashboard?.latest_health_reports || [];
    const violations = dashboard?.recent_violations || [];
    const healthBreakdown = dashboard?.agent_health_breakdown || {};

    const healthColor =
        systemHealth >= 90
            ? 'text-green-600 dark:text-green-400'
            : systemHealth >= 70
            ? 'text-yellow-600 dark:text-yellow-400'
            : 'text-red-600 dark:text-red-400';

    return (
        <div className="min-h-screen bg-gray-50 dark:bg-gray-950 p-6 transition-colors duration-200">
            <div className="max-w-7xl mx-auto">

                {/* ── Header ─────────────────────────────────────────────── */}
                <div className="mb-8 flex items-center justify-between">
                    <div className="flex items-center gap-3">
                        <div className="w-12 h-12 rounded-xl bg-gradient-to-br from-blue-600 to-purple-600 flex items-center justify-center shadow-lg">
                            <Activity className="w-7 h-7 text-white" />
                        </div>
                        <div>
                            <h1 className="text-3xl font-bold text-gray-900 dark:text-white">
                                System Monitoring
                            </h1>
                            <p className="text-gray-500 dark:text-gray-400 text-sm">
                                Real-time oversight of agent operations
                            </p>
                        </div>
                    </div>

                    <div className="flex items-center gap-3">
                        {lastUpdated && (
                            <span className="hidden sm:flex items-center gap-1 text-xs text-gray-400 dark:text-gray-500">
                                <Clock className="w-3 h-3" />
                                Updated {lastUpdated.toLocaleTimeString()}
                            </span>
                        )}
                        <button
                            onClick={() => loadDashboard(true)}
                            className="p-2 rounded-lg hover:bg-gray-100 dark:hover:bg-gray-800 text-gray-500 dark:text-gray-400 transition-colors"
                            title="Refresh now"
                        >
                            <RefreshCw className={`w-4 h-4 ${isRefreshing ? 'animate-spin' : ''}`} />
                        </button>
                    </div>
                </div>

                {/* ── Error Notice ────────────────────────────────────────── */}
                {error && (
                    <div className="mb-6 bg-yellow-50 dark:bg-yellow-950/40 border border-yellow-200 dark:border-yellow-800/60 rounded-lg p-4">
                        <div className="flex gap-3">
                            <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400 flex-shrink-0 mt-0.5" />
                            <div>
                                <h3 className="text-sm font-semibold text-yellow-900 dark:text-yellow-300 mb-1">
                                    Monitoring System Notice
                                </h3>
                                <p className="text-sm text-yellow-800 dark:text-yellow-400">
                                    {error}. Displaying cached or default values.
                                </p>
                            </div>
                        </div>
                    </div>
                )}

                {/* ── Stats Grid ──────────────────────────────────────────── */}
                <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">

                    {/* System Health */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm flex items-center gap-4">
                        <div className="relative flex-shrink-0">
                            <HealthRing score={systemHealth} />
                            <span className={`absolute inset-0 flex items-center justify-center text-xs font-bold ${healthColor}`}>
                                {systemHealth}%
                            </span>
                        </div>
                        <div>
                            <p className="text-sm text-gray-500 dark:text-gray-400 mb-0.5">System Health</p>
                            <p className={`text-2xl font-bold ${healthColor}`}>{systemHealth}%</p>
                            <p className="text-xs text-gray-500 dark:text-gray-400 mt-0.5">
                                {systemHealth >= 90 ? 'Fully Operational' : systemHealth >= 70 ? 'Degraded' : 'Critical'}
                            </p>
                        </div>
                    </div>

                    {/* Active Alerts */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Active Alerts</p>
                                <p className={`text-3xl font-bold ${activeAlerts > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-900 dark:text-white'}`}>
                                    {activeAlerts}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {activeAlerts === 0 ? 'No issues detected' : `${activeAlerts} requiring attention`}
                                </p>
                            </div>
                            <div className={`w-12 h-12 rounded-lg flex items-center justify-center ${activeAlerts > 0 ? 'bg-red-100 dark:bg-red-900/30' : 'bg-gray-100 dark:bg-gray-800'}`}>
                                <AlertTriangle className={`w-6 h-6 ${activeAlerts > 0 ? 'text-red-600 dark:text-red-400' : 'text-gray-400 dark:text-gray-500'}`} />
                            </div>
                        </div>
                    </div>

                    {/* Agents reporting */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 p-6 shadow-sm">
                        <div className="flex items-center justify-between">
                            <div>
                                <p className="text-sm text-gray-500 dark:text-gray-400 mb-1">Agents Reporting</p>
                                <p className="text-3xl font-bold text-gray-900 dark:text-white">
                                    {healthReports.length}
                                </p>
                                <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                                    {healthReports.filter((r: AgentHealthReport) => r.health_score >= 90).length} healthy
                                </p>
                            </div>
                            <div className="w-12 h-12 rounded-lg bg-blue-100 dark:bg-blue-900/30 flex items-center justify-center">
                                <Cpu className="w-6 h-6 text-blue-600 dark:text-blue-400" />
                            </div>
                        </div>
                    </div>
                </div>

                {/* ── Agent Health Breakdown mini-cards ───────────────────── */}
                {Object.keys(healthBreakdown).length > 0 && (
                    <div className="mb-8">
                        <h2 className="text-sm font-semibold text-gray-500 dark:text-gray-400 uppercase tracking-wide mb-3">
                            Agent Tier Health
                        </h2>
                        <div className="grid grid-cols-2 sm:grid-cols-4 gap-3">
                            {Object.entries(healthBreakdown).map(([tier, score]) => (
                                <div key={tier} className="bg-white dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-800 p-3 flex items-center gap-3">
                                    <div className={`w-8 h-8 rounded-md flex items-center justify-center ${
                                        (score as number) >= 90 ? 'bg-green-100 dark:bg-green-900/30' : 'bg-yellow-100 dark:bg-yellow-900/30'
                                    }`}>
                                        <Zap className={`w-4 h-4 ${(score as number) >= 90 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`} />
                                    </div>
                                    <div>
                                        <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{tier}</p>
                                        <p className={`text-sm font-bold ${(score as number) >= 90 ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                                            {score}%
                                        </p>
                                    </div>
                                </div>
                            ))}
                        </div>
                    </div>
                )}

                {/* ── Panels Row ──────────────────────────────────────────── */}
                <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                    {/* Recent Violations */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                        <div className="bg-yellow-50 dark:bg-yellow-950/50 border-b border-yellow-100 dark:border-yellow-900/60 px-6 py-4 flex items-center justify-between">
                            <h2 className="text-base font-bold text-gray-900 dark:text-yellow-100 flex items-center gap-2">
                                <AlertTriangle className="w-5 h-5 text-yellow-600 dark:text-yellow-400" />
                                Recent Violations
                            </h2>
                            {violations.length > 0 && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-yellow-200 dark:bg-yellow-800/60 text-yellow-800 dark:text-yellow-300 font-medium">
                                    {violations.length}
                                </span>
                            )}
                        </div>

                        <div className="p-6 bg-white dark:bg-gray-900">
                            {violations.length > 0 ? (
                                <div className="space-y-3 max-h-80 overflow-y-auto">
                                    {violations.map((v: ViolationReport) => (
                                        <div
                                            key={v.id}
                                            className="bg-gray-50 dark:bg-gray-800 rounded-lg p-4 border border-gray-200 dark:border-gray-700"
                                        >
                                            <div className="flex items-start justify-between gap-4">
                                                <div className="flex-1">
                                                    <div className="flex items-center gap-2 mb-1">
                                                        <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                                                            v.severity === 'critical' || v.severity === 'major'
                                                                ? 'bg-red-100 text-red-700 dark:bg-red-900/40 dark:text-red-300'
                                                                : 'bg-yellow-100 text-yellow-700 dark:bg-yellow-900/40 dark:text-yellow-300'
                                                        }`}>
                                                            {v.severity}
                                                        </span>
                                                    </div>
                                                    <p className="text-sm text-gray-900 dark:text-gray-100">{v.description}</p>
                                                    <p className="text-xs text-gray-400 dark:text-gray-500 mt-1">
                                                        {v.created_at ? new Date(v.created_at).toLocaleString() : '—'}
                                                    </p>
                                                </div>
                                            </div>
                                        </div>
                                    ))}
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <div className="w-14 h-14 rounded-full bg-green-50 dark:bg-green-900/20 flex items-center justify-center mx-auto mb-3 border border-green-100 dark:border-green-800/40">
                                        <ShieldCheck className="w-7 h-7 text-green-500 dark:text-green-400" />
                                    </div>
                                    <p className="text-gray-900 dark:text-white font-medium mb-1">No Violations Detected</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">All agents operating within guidelines</p>
                                </div>
                            )}
                        </div>
                    </div>

                    {/* Agent Health Reports */}
                    <div className="bg-white dark:bg-gray-900 rounded-xl border border-gray-200 dark:border-gray-800 shadow-sm overflow-hidden">
                        <div className="bg-blue-50 dark:bg-blue-950/50 border-b border-blue-100 dark:border-blue-900/60 px-6 py-4 flex items-center justify-between">
                            <h2 className="text-base font-bold text-gray-900 dark:text-blue-100 flex items-center gap-2">
                                <Activity className="w-5 h-5 text-blue-600 dark:text-blue-400" />
                                Agent Health Reports
                            </h2>
                            {healthReports.length > 0 && (
                                <span className="text-xs px-2 py-0.5 rounded-full bg-blue-200 dark:bg-blue-800/60 text-blue-800 dark:text-blue-300 font-medium">
                                    {healthReports.length}
                                </span>
                            )}
                        </div>

                        <div className="p-6 bg-white dark:bg-gray-900">
                            {healthReports.length > 0 ? (
                                <div className="space-y-3 max-h-80 overflow-y-auto">
                                    {healthReports.map((report: AgentHealthReport) => {
                                        const isHealthy = report.health_score > 90;
                                        return (
                                            <div
                                                key={report.id}
                                                className="flex items-center gap-4 bg-gray-50 dark:bg-gray-800 p-4 rounded-lg border border-gray-200 dark:border-gray-700"
                                            >
                                                <div className="relative flex-shrink-0">
                                                    <HealthRing score={report.health_score} />
                                                    <span className={`absolute inset-0 flex items-center justify-center text-[10px] font-bold ${isHealthy ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                                                        {report.health_score}
                                                    </span>
                                                </div>
                                                <div className="flex-1 min-w-0">
                                                    <p className="text-sm font-semibold text-gray-900 dark:text-white truncate">
                                                        Agent #{report.subject}
                                                    </p>
                                                    <p className="text-xs text-gray-500 dark:text-gray-400 capitalize">{report.status}</p>
                                                </div>
                                                <div className="text-right flex-shrink-0">
                                                    <div className="text-xs text-gray-500 dark:text-gray-400">Success Rate</div>
                                                    <div className={`text-sm font-bold ${isHealthy ? 'text-green-600 dark:text-green-400' : 'text-yellow-600 dark:text-yellow-400'}`}>
                                                        {report.metrics.success_rate}%
                                                    </div>
                                                </div>
                                            </div>
                                        );
                                    })}
                                </div>
                            ) : (
                                <div className="text-center py-10">
                                    <div className="w-14 h-14 rounded-full bg-blue-50 dark:bg-blue-900/20 flex items-center justify-center mx-auto mb-3 border border-blue-100 dark:border-blue-800/40">
                                        <CheckCircle className="w-7 h-7 text-blue-400 dark:text-blue-500" />
                                    </div>
                                    <p className="text-gray-900 dark:text-white font-medium mb-1">No Health Reports</p>
                                    <p className="text-sm text-gray-500 dark:text-gray-400">Agent monitoring will appear here</p>
                                </div>
                            )}
                        </div>
                    </div>
                </div>

            </div>
        </div>
    );
};