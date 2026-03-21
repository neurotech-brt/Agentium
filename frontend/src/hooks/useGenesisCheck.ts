/**
 * useGenesisCheck
 *
 * Fires exactly once per login session, immediately after the user becomes
 * authenticated. If the backend reports no API key is configured, shows a
 * toast and redirects to /models so the user knows exactly what to do.
 *
 * sessionStorage is the correct scope here:
 *   - survives re-renders and React StrictMode double-invocations
 *   - clears when the tab closes → a new login always re-checks
 *   - authStore.logout() removes the key so the next login also re-checks
 */

import { useEffect } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';

const SESSION_KEY = 'genesis_check_done';

export function useGenesisCheck() {
    const navigate = useNavigate();
    // Only subscribe to the boolean we actually need — avoids re-running the
    // effect every time an unrelated field on the user object changes.
    const isAuthenticated = useAuthStore((s) => s.user?.isAuthenticated);

    useEffect(() => {
        if (!isAuthenticated) return;

        // Guard: only run once per login session
        if (sessionStorage.getItem(SESSION_KEY)) return;

        // Mark immediately — prevents React StrictMode double-fire from
        // sending two requests and triggering two redirects.
        sessionStorage.setItem(SESSION_KEY, 'true');

        // authStore stores the token under 'access_token' (see authStore.ts)
        const token = localStorage.getItem('access_token');

        fetch('/api/v1/genesis/status', {
            headers: { Authorization: `Bearer ${token}` },
        })
            .then((r) => r.json())
            .then((data) => {
                if (data.status === 'no_api_key') {
                    toast('Add an AI provider key to begin Genesis.', {
                        icon: '🔑',
                        duration: 6000,
                    });
                    // replace: true — back button won't loop the user back here
                    navigate('/models', { replace: true });
                }
            })
            .catch(() => {
                // Non-fatal: if the check fails don't block the user.
                // The guard flag is already set so this won't retry.
            });
    }, [isAuthenticated, navigate]);
}