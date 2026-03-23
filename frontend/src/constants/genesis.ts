/**
 * Genesis session-storage key constants.
 *
 * Kept in a standalone file so both authStore.ts and useGenesisCheck.ts
 * can import from here without creating a circular dependency.
 *
 * Circular dependency that was broken:
 *   authStore.ts → useGenesisCheck.ts → authStore.ts  ❌
 *
 * After fix:
 *   authStore.ts     → constants/genesis.ts  ✅
 *   useGenesisCheck  → constants/genesis.ts  ✅
 */

/**
 * Set once genesis reaches "ready".
 * Guards the entire hook from running once the system is fully initialized.
 */
export const GENESIS_SESSION_KEY = 'genesis_check_done';

/**
 * Set the first time we redirect to /models because no API key is configured.
 * Prevents repeated redirects on the same login session (including after
 * page refreshes). Cleared when a key is added or the user logs out.
 */
export const GENESIS_REDIRECT_KEY = 'genesis_redirected_to_models';