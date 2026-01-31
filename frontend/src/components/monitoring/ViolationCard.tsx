import React from 'react';
import { ViolationReport } from '../../types';
import { AlertOctagon, AlertTriangle, ShieldAlert, Info } from 'lucide-react';

interface ViolationCardProps {
    violation: ViolationReport;
}

export const ViolationCard: React.FC<ViolationCardProps> = ({ violation }) => {
    const getSeverityDetails = () => {
        switch (violation.severity) {
            case 'critical': return { color: 'red', icon: <AlertOctagon className="w-5 h-5" /> };
            case 'major': return { color: 'orange', icon: <ShieldAlert className="w-5 h-5" /> };
            case 'moderate': return { color: 'yellow', icon: <AlertTriangle className="w-5 h-5" /> };
            default: return { color: 'blue', icon: <Info className="w-5 h-5" /> };
        }
    };

    const details = getSeverityDetails();

    return (
        <div className={`bg-gray-800 rounded-lg p-4 border border-${details.color}-500/30 hover:border-${details.color}-500/50 transition-colors`}>
            <div className="flex justify-between items-start mb-2">
                <div className={`flex items-center gap-2 text-${details.color}-400 font-bold uppercase text-xs tracking-wider`}>
                    {details.icon}
                    {violation.severity} Severity
                </div>
                <span className="text-gray-500 text-xs">{new Date(violation.created_at).toLocaleDateString()}</span>
            </div>

            <h4 className="text-white font-medium mb-1">{violation.type.replace(/_/g, ' ')}</h4>
            <p className="text-gray-400 text-sm mb-3">{violation.description}</p>

            <div className="flex justify-between items-center text-xs bg-gray-900/50 p-2 rounded">
                <div>
                    <span className="text-gray-500 block">Violator</span>
                    <span className="text-gray-300 font-mono">#{violation.violator}</span>
                </div>
                <div>
                    <span className="text-gray-500 block">Status</span>
                    <span className="text-white capitalize">{violation.status}</span>
                </div>
            </div>
        </div>
    );
};
