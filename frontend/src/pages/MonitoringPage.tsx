import React, { useEffect, useState } from 'react';
import { monitoringService } from '../services/monitoring';
import { MonitoringDashboard } from '../types';
import { HealthScore } from '../components/monitoring/HealthScore';
import { ViolationCard } from '../components/monitoring/ViolationCard';
import { Activity, ShieldCheck, AlertTriangle } from 'lucide-react';

export const MonitoringPage: React.FC = () => {
    const [dashboard, setDashboard] = useState<MonitoringDashboard | null>(null);
    const [isLoading, setIsLoading] = useState(true);

    useEffect(() => {
        loadDashboard();
    }, []);

    const loadDashboard = async () => {
        try {
            // "00001" is Head of Council, usually the top monitor
            const data = await monitoringService.getDashboard('00001');
            setDashboard(data);
        } catch (err) {
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    if (isLoading) return <div className="p-6 text-center text-gray-500">Loading metrics...</div>;

    // Fallback if no data (e.g. fresh system)
    const systemHealth = dashboard?.system_health || 100;
    const activeAlerts = dashboard?.active_alerts || 0;

    return (
        <div className="p-6 h-full overflow-auto">
            <h1 className="text-3xl font-bold text-white mb-2">System Monitoring</h1>
            <p className="text-gray-400 mb-8">Real-time oversight of agent operations</p>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-8">
                {/* System Health Card */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 flex items-center justify-between">
                    <div>
                        <h3 className="text-gray-400 text-sm font-medium mb-1">Overall System Health</h3>
                        <p className={`text-2xl font-bold ${systemHealth > 90 ? 'text-green-400' : 'text-yellow-400'}`}>
                            {systemHealth > 90 ? 'Operational' : 'Degraded'}
                        </p>
                    </div>
                    <HealthScore score={systemHealth} size="sm" />
                </div>

                {/* Active Alerts Card */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 flex items-center justify-between">
                    <div>
                        <h3 className="text-gray-400 text-sm font-medium mb-1">Active Alerts</h3>
                        <p className="text-3xl font-bold text-white">{activeAlerts}</p>
                    </div>
                    <div className="p-3 bg-red-500/10 rounded-lg">
                        <Activity className="w-8 h-8 text-red-500" />
                    </div>
                </div>

                {/* Agent Count Card */}
                <div className="bg-gray-800 rounded-xl p-6 border border-gray-700 flex items-center justify-between">
                    <div>
                        <h3 className="text-gray-400 text-sm font-medium mb-1">Monitored Agents</h3>
                        <p className="text-3xl font-bold text-white">
                            {dashboard?.latest_health_reports.length || 0}
                        </p>
                    </div>
                    <div className="p-3 bg-blue-500/10 rounded-lg">
                        <ShieldCheck className="w-8 h-8 text-blue-500" />
                    </div>
                </div>
            </div>

            <div className="grid grid-cols-1 lg:grid-cols-2 gap-8">
                {/* Recent Violations */}
                <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <AlertTriangle className="w-5 h-5 text-yellow-500" />
                        Recent Violations
                    </h2>
                    <div className="space-y-4">
                        {dashboard?.recent_violations && dashboard.recent_violations.length > 0 ? (
                            dashboard.recent_violations.map(v => (
                                <ViolationCard key={v.id} violation={v} />
                            ))
                        ) : (
                            <div className="text-center py-10 text-gray-500 bg-gray-800/30 rounded border border-gray-800 border-dashed">
                                No recent violations detected.
                            </div>
                        )}
                    </div>
                </div>

                {/* Agent Health List */}
                <div className="bg-gray-900/50 rounded-xl border border-gray-800 p-6">
                    <h2 className="text-xl font-bold text-white mb-4 flex items-center gap-2">
                        <Activity className="w-5 h-5 text-blue-500" />
                        Agent Health Reports
                    </h2>
                    <div className="space-y-3">
                        {dashboard?.latest_health_reports && dashboard.latest_health_reports.length > 0 ? (
                            dashboard.latest_health_reports.map(report => (
                                <div key={report.id} className="flex items-center justify-between bg-gray-800 p-3 rounded border border-gray-700">
                                    <div className="flex items-center gap-3">
                                        <HealthScore score={report.health_score} size="sm" />
                                        {/* Should make size even smaller or custom css for list items maybe? 'sm' is 16x16 which is okay for icon but svg is bigger in component. Let's adjust component if needed or use flex scale. Actually size 'sm' in HealthScore is w-16 h-16 (4rem). That's big for a list item. */}
                                        <div>
                                            <p className="text-white font-medium">Agent #{report.subject}</p>
                                            <p className="text-xs text-gray-400 capitalize">{report.status}</p>
                                        </div>
                                    </div>
                                    <div className="text-right">
                                        <div className="text-xs text-gray-500">Success Rate</div>
                                        <div className="text-green-400 font-medium">{report.metrics.success_rate}%</div>
                                    </div>
                                </div>
                            ))
                        ) : (
                            <div className="text-center py-10 text-gray-500 bg-gray-800/30 rounded border border-gray-800 border-dashed">
                                No health reports available.
                            </div>
                        )}
                    </div>
                </div>
            </div>
        </div>
    );
};
