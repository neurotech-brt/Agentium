import React from 'react';
import { HeartPulse } from 'lucide-react';

interface HealthScoreProps {
    score: number;
    size?: 'sm' | 'md' | 'lg';
}

export const HealthScore: React.FC<HealthScoreProps> = ({ score, size = 'md' }) => {
    const getColor = (s: number) => {
        if (s >= 90) return 'text-green-500';
        if (s >= 70) return 'text-blue-500';
        if (s >= 50) return 'text-yellow-500';
        return 'text-red-500';
    };

    const getBgColor = (s: number) => {
        if (s >= 90) return 'stroke-green-500';
        if (s >= 70) return 'stroke-blue-500';
        if (s >= 50) return 'stroke-yellow-500';
        return 'stroke-red-500';
    };

    const radius = 40;
    const circumference = 2 * Math.PI * radius;
    const offset = circumference - (score / 100) * circumference;

    const sizeClasses = {
        sm: 'w-16 h-16',
        md: 'w-24 h-24',
        lg: 'w-32 h-32'
    };

    return (
        <div className={`relative flex items-center justify-center ${sizeClasses[size]}`}>
            <svg className="transform -rotate-90 w-full h-full">
                <circle
                    className="text-gray-700 stroke-current"
                    strokeWidth="8" // Thicker stroke
                    cx="50%"
                    cy="50%"
                    r={radius}
                    fill="transparent"
                />
                <circle
                    className={`${getBgColor(score)} transition-all duration-1000 ease-out`}
                    strokeWidth="8"
                    strokeDasharray={circumference}
                    strokeDashoffset={offset}
                    strokeLinecap="round"
                    cx="50%"
                    cy="50%"
                    r={radius}
                    fill="transparent"
                />
            </svg>
            <div className="absolute flex flex-col items-center justify-center">
                <HeartPulse className={`w-5 h-5 ${getColor(score)} mb-1 opacity-80`} />
                <span className={`font-bold text-white ${size === 'sm' ? 'text-sm' : size === 'lg' ? 'text-2xl' : 'text-xl'}`}>
                    {Math.round(score)}%
                </span>
            </div>
        </div>
    );
};
