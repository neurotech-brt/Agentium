/**
 * frontend/src/utils/agentIds.ts
 *
 * Utilities for working with Agentium ID prefixes.
 *
 * Tier prefixes
 * -------------
 *   0xxxx  Head of Council
 *   1xxxx  Council Members
 *   2xxxx  Lead Agents
 *   3xxxx  Task Agents
 *   4xxxx  (legacy) Code Critics (permanent singletons — deprecated)
 *   5xxxx  (legacy) Output Critics (permanent singletons — deprecated)
 *   6xxxx  (legacy) Plan Critics (permanent singletons — deprecated)
 *   7xxxx  Code Critics (ephemeral, per-task)
 *   8xxxx  Output Critics (ephemeral, per-task)
 *   9xxxx  Plan Critics (ephemeral, per-task)
 */

/** Returns true for any critic agent (legacy 4/5/6 or ephemeral 7/8/9). */
export function isCriticAgentId(id: string | null | undefined): boolean {
  if (!id) return false;
  return ['4', '5', '6', '7', '8', '9'].includes(id[0]);
}

/** Returns true only for the ephemeral per-task critics (7/8/9 prefix). */
export function isEphemeralCriticId(id: string | null | undefined): boolean {
  if (!id) return false;
  return ['7', '8', '9'].includes(id[0]);
}

/** Returns true only for the legacy singleton critics (4/5/6 prefix). */
export function isLegacyCriticId(id: string | null | undefined): boolean {
  if (!id) return false;
  return ['4', '5', '6'].includes(id[0]);
}

/** Returns a human-readable label for a critic prefix. */
export function criticTypeLabel(id: string | null | undefined): string {
  if (!id) return 'Unknown Critic';
  switch (id[0]) {
    case '4': case '7': return 'Code Critic';
    case '5': case '8': return 'Output Critic';
    case '6': case '9': return 'Plan Critic';
    default: return 'Critic';
  }
}

/** Returns the tier number (0–3) for governance agents, null for critics. */
export function agentTierNumber(id: string | null | undefined): number | null {
  if (!id) return null;
  const prefix = id[0];
  if (['4','5','6','7','8','9'].includes(prefix)) return null;
  const tier = parseInt(prefix, 10);
  return isNaN(tier) ? null : tier;
}