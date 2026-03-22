/**
 * useGenesisCheck
 *
 * Fires once per login session (guarded by sessionStorage) immediately after
 * the user becomes authenticated. Handles three backend states:
 *
 *   no_api_key  → toast + redirect to /models so the user adds a key
 *   pending     → API key exists but genesis not run → trigger POST /initialize
 *   ready       → fully operational, do nothing
 *
 * Session guard rules:
 *   - Set INSIDE the success callback (not before the fetch), so any network
 *     failure leaves the key unset and the check retries on the next navigation.
 *   - Cleared by authStore.logout() so the next login always re-checks.
 *   - Cleared by saveModelConfig() (see useModelConfigs) so that adding an API
 *     key on /models immediately re-evaluates on the next render.
 *
 * Genesis polling:
 *   After triggering POST /initialize the hook polls GET /status every 3 s
 *   until status === "ready" (or up to MAX_POLL_ATTEMPTS attempts). A toast
 *   notifies the user when the system finishes bootstrapping.
 */

import { useEffect, useRef } from 'react';
import { useNavigate } from 'react-router-dom';
import toast from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';

const SESSION_KEY          = 'genesis_check_done';
const POLL_INTERVAL_MS     = 3_000;
const MAX_POLL_ATTEMPTS    = 20;   // 60 s total ceiling

export function useGenesisCheck() {
    const navigate        = useNavigate();
    const isAuthenticated = useAuthStore((s) => s.user?.isAuthenticated);
    const pollTimerRef    = useRef<ReturnType<typeof setTimeout> | null>(null);

    // Clean up any in-flight polling timer when the component unmounts
    useEffect(() => () => {
        if (pollTimerRef.current) clearTimeout(pollTimerRef.current);
    }, []);

    useEffect(() => {
        if (!isAuthenticated) return;
        if (sessionStorage.getItem(SESSION_KEY)) return;

        const token = localStorage.getItem('access_token');
        if (!token) return;

        const authHeaders = { Authorization: `Bearer ${token}` };

        // ── Poll until status === "ready" ─────────────────────────────────────
        let attempts = 0;
        function pollUntilReady() {
            if (attempts >= MAX_POLL_ATTEMPTS) {
                toast.error('Genesis is taking longer than expected. Please refresh.');
                return;
            }
            attempts += 1;
            pollTimerRef.current = setTimeout(async () => {
                try {
                    const r = await fetch('/api/v1/genesis/status', { headers: authHeaders });
                    if (!r.ok) return;                          // transient error — retry
                    const data = await r.json();
                    if (data.status === 'ready') {
                        sessionStorage.setItem(SESSION_KEY, 'true');
                        toast.success('System initialized and ready.', { icon: '🏛️', duration: 5_000 });
                    } else {
                        pollUntilReady();                       // still pending — keep polling
                    }
                } catch {
                    pollUntilReady();                           // network glitch — retry
                }
            }, POLL_INTERVAL_MS);
        }

        // ── Main status check ─────────────────────────────────────────────────
        fetch('/api/v1/genesis/status', { headers: authHeaders })
            .then((r) => {
                if (!r.ok) throw new Error(`HTTP ${r.status}`);
                return r.json();
            })
            .then(async (data) => {
                // ── Case 1: No API key — redirect to /models ──────────────────
                if (data.status === 'no_api_key') {
                    // Mark done so the toast/redirect fires only once per session.
                    sessionStorage.setItem(SESSION_KEY, 'true');
                    toast('Add an AI provider key to begin Genesis.', {
                        icon: '🔑',
                        duration: 6_000,
                    });
                    navigate('/models', { replace: true });
                    return;
                }

                // ── Case 2: Key exists but genesis not run → trigger it ────────
                if (data.status === 'pending') {
                    try {
                        const initRes = await fetch('/api/v1/genesis/initialize', {
                            method:  'POST',
                            headers: authHeaders,
                        });
                        if (initRes.ok) {
                            const initData = await initRes.json();
                            if (initData.status === 'already_initialized') {
                                // Race condition: another tab finished first
                                sessionStorage.setItem(SESSION_KEY, 'true');
                            } else {
                                // "started" — poll until ready
                                toast('Initializing Agentium governance system…', {
                                    icon: '🏛️',
                                    duration: 4_000,
                                });
                                pollUntilReady();
                            }
                        }
                    } catch (err) {
                        console.warn('[GenesisCheck] Failed to trigger initialization:', err);
                        // Leave session key unset so we retry on next navigation
                    }
                    return;
                }

                // ── Case 3: Already ready ──────────────────────────────────────
                if (data.status === 'ready') {
                    sessionStorage.setItem(SESSION_KEY, 'true');
                }
            })
            .catch((err) => {
                // Network or auth failure — leave key unset so we retry
                console.warn('[GenesisCheck] Status check failed, will retry:', err);
                sessionStorage.removeItem(SESSION_KEY);
            });

    }, [isAuthenticated, navigate]);
}