import { create } from 'zustand';
import { persist } from 'zustand/middleware';
import { api } from '@/services/api';
import { jwtDecode } from 'jwt-decode'; // Install this package: npm install jwt-decode

interface User {
    id: string;
    username: string;
    role: string;
    isAuthenticated: boolean;
    isSovereign?: boolean;
    agentium_id?: string; // ✅ NEW: Stores the agent ID for tier-based access
}

interface AuthState {
    user: User | null;
    login: (username: string, password: string) => Promise<boolean>;
    logout: () => void;
    changePassword: (oldPassword: string, newPassword: string) => Promise<boolean>;
    isLoading: boolean;
    error: string | null;
    checkAuth: () => Promise<boolean>;
}

// Helper to decode JWT and extract agentium_id
const extractAgentFromToken = (token: string): string | null => {
    try {
        const decoded = jwtDecode<any>(token);
        return decoded.agentium_id || null;
    } catch {
        return null;
    }
};

export const useAuthStore = create<AuthState>()(
    persist(
        (set, get) => ({
            user: null,
            isLoading: false,
            error: null,

            login: async (username: string, password: string) => {
                set({ isLoading: true, error: null });

                try {
                    // ✅ FIXED: Changed to /api/v1/auth/login (added /api/v1 prefix)
                    const response = await api.post('/api/v1/auth/login', {
                        username,
                        password
                    });

                    const { access_token, user } = response.data;

                    // Store JWT token
                    localStorage.setItem('access_token', access_token);

                    // Extract agentium_id from token if not in user object
                    const agentiumId = user.agentium_id || extractAgentFromToken(access_token);

                    set({
                        user: {
                            ...user,
                            isAuthenticated: true,
                            agentium_id: agentiumId, // ✅ Store agentium_id
                            isSovereign: agentiumId ? agentiumId.startsWith('0') : false // ✅ Sovereign if agentium_id starts with 0
                        },
                        isLoading: false,
                        error: null
                    });

                    return true;
                } catch (error: any) {
                    set({
                        error: error.response?.data?.detail || 'Invalid credentials',
                        isLoading: false
                    });
                    return false;
                }
            },

            logout: () => {
                localStorage.removeItem('access_token');
                set({ user: null, error: null });
            },

            changePassword: async (oldPassword: string, newPassword: string) => {
                set({ isLoading: true, error: null });

                try {
                    // ✅ FIXED: Changed to /api/v1/auth/change-password
                    await api.post('/api/v1/auth/change-password', {
                        old_password: oldPassword,
                        new_password: newPassword
                    });

                    set({ isLoading: false, error: null });
                    return true;
                } catch (error: any) {
                    set({
                        error: error.response?.data?.detail || 'Failed to change password',
                        isLoading: false
                    });
                    return false;
                }
            },

            checkAuth: async () => {
                const token = localStorage.getItem('access_token');
                if (!token) {
                    set({ user: null });
                    return false;
                }

                try {
                    // ✅ FIXED: Changed to /api/v1/auth/verify
                    const response = await api.post('/api/v1/auth/verify', { token });

                    if (response.data.valid) {
                        const userData = response.data.user;
                        const agentiumId = userData.agentium_id || extractAgentFromToken(token);

                        set({
                            user: {
                                ...userData,
                                isAuthenticated: true,
                                agentium_id: agentiumId, // ✅ Store agentium_id
                                isSovereign: agentiumId ? agentiumId.startsWith('0') : false
                            },
                            error: null
                        });
                        return true;
                    } else {
                        localStorage.removeItem('access_token');
                        set({ user: null });
                        return false;
                    }
                } catch (error) {
                    localStorage.removeItem('access_token');
                    set({ user: null });
                    return false;
                }
            }
        }),
        {
            name: 'auth-storage',
            partialize: (state) => ({
                user: state.user
            })
        }
    )
);