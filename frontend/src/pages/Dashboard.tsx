// ─── Dashboard ───────────────────────────────────────────────────────────────

import { useBackendStore }  from '@/store/backendStore';
import APIKeyHealth          from '@/components/monitoring/APIKeyHealth';
import BudgetControl         from '@/components/BudgetControl';
import { ChannelHealthWidget } from '@/components/dashboard/ChannelHealthWidget';
import { ProviderAnalytics }   from '@/components/dashboard/ProviderAnalytics';
import { ErrorBoundary }       from '@/components/common/ErrorBoundary';

// ── New extracted sub-components ──────────────────────────────────────────────
import { DashboardHeader } from '@/components/dashboard/DashboardHeader';
import { StatsGrid }       from '@/components/dashboard/StatsGrid';
import { RecentTasks }     from '@/components/dashboard/RecentTasks';
import { AgentsList }      from '@/components/dashboard/AgentsList';
import { SystemHealth }    from '@/components/dashboard/SystemHealth';
import { QuickActions }    from '@/components/dashboard/QuickActions';

// ── Custom hook ───────────────────────────────────────────────────────────────
import { useDashboardData } from '@/hooks/useDashboardData';

export function Dashboard() {
    const { status } = useBackendStore();

    const {
        stats,
        recentTasks,
        activeAgentsList,
        isAgentsLoading,
        isTasksLoading,
        isAgentsError,
        isTasksError,
        refetchAgents,
        refetchTasks,
    } = useDashboardData();

    // Show loading skeletons in the stat cards while the backend is not yet
    // connected OR while either query is on its very first fetch.
    const statsLoading =
        status.status !== 'connected' ||
        isAgentsLoading                ||
        isTasksLoading;

    return (
        <div className="h-full bg-gray-50 dark:bg-[#0f1117] p-6 transition-colors duration-200">

            {/* ── Welcome header + disconnect banner ──────────────────────── */}
            <DashboardHeader />

            {/* ── KPI stat cards ──────────────────────────────────────────── */}
            <ErrorBoundary variant="widget" fallbackHeading="Stats Error">
                <StatsGrid stats={stats} isLoading={statsLoading} />
            </ErrorBoundary>

            {/* ── Provider analytics ──────────────────────────────────────── */}
            {/* Preserved in original position.                               */}
            <div className="mb-8">
                <ErrorBoundary variant="widget" fallbackHeading="Analytics Error">
                    <ProviderAnalytics />
                </ErrorBoundary>
            </div>

            {/* ── Budget control panel ────────────────────────────────────── */}
            <div className="mb-8">
                <ErrorBoundary variant="widget" fallbackHeading="Budget Control Error">
                    <BudgetControl />
                </ErrorBoundary>
            </div>

            {/* ── API key health ──────────────────────────────────────────── */}
            <div className="mb-8">
                <ErrorBoundary variant="widget" fallbackHeading="API Key Health Error">
                    <APIKeyHealth />
                </ErrorBoundary>
            </div>

            {/* ── Channel health ──────────────────────────────────────────── */}
            <div className="mb-8">
                <ErrorBoundary variant="widget" fallbackHeading="Channel Health Error">
                    <ChannelHealthWidget />
                </ErrorBoundary>
            </div>

            {/* ── Live activity row: Recent Tasks + Active Agents ─────────── */}
            {/* New section — gives the operator an at-a-glance status view   */}
            {/* without navigating away from the dashboard.                   */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6 mb-6">
                <ErrorBoundary variant="widget" fallbackHeading="Recent Tasks Error">
                    <RecentTasks
                        tasks={recentTasks}
                        isLoading={isTasksLoading}
                        isError={isTasksError}
                        onRetry={refetchTasks}
                    />
                </ErrorBoundary>
                <ErrorBoundary variant="widget" fallbackHeading="Active Agents Error">
                    <AgentsList
                        agents={activeAgentsList}
                        isLoading={isAgentsLoading}
                        isError={isAgentsError}
                        onRetry={refetchAgents}
                    />
                </ErrorBoundary>
            </div>

            {/* ── Bottom panels: System Status + Quick Actions ─────────────  */}
            {/* Preserved in original position with identical visual output.  */}
            <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
                <ErrorBoundary variant="widget" fallbackHeading="System Health Error">
                    <SystemHealth />
                </ErrorBoundary>
                <ErrorBoundary variant="widget" fallbackHeading="Quick Actions Error">
                    <QuickActions />
                </ErrorBoundary>
            </div>

        </div>
    );
}