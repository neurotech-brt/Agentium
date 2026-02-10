import { Navigate } from 'react-router-dom';
import { useAuthStore } from '@/store/authStore';

interface SovereignRouteProps {
    children: React.ReactNode;
}

export function SovereignRoute({ children }: SovereignRouteProps) {
    const { user } = useAuthStore();

    // Not logged in at all — send to login
    if (!user?.isAuthenticated) {
        return <Navigate to="/login" replace />;
    }

    // Logged in but not sovereign — send back to dashboard
    if (!user?.isSovereign) {
        return <Navigate to="/" replace />;
    }

    return <>{children}</>;
}