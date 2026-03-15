/**
 * frontend/src/utils/time.ts
 *
 * Shared time-formatting utilities.
 * Extracted from inline MessageRow logic so the function is testable
 * and reusable across pages (Tasks, Monitoring, etc.).
 */

/**
 * Converts an ISO timestamp string into a human-readable relative time string.
 *
 * Examples:
 *   "45s ago"  — less than 1 minute
 *   "12m ago"  — less than 1 hour
 *   "3h ago"   — less than 24 hours
 *   "Jan 4, 2024" — 24 hours or older (locale date string)
 */
export function getRelativeTime(isoString: string): string {
  const diff = (Date.now() - new Date(isoString).getTime()) / 1000;
  if (diff < 60)    return `${Math.floor(diff)}s ago`;
  if (diff < 3600)  return `${Math.floor(diff / 60)}m ago`;
  if (diff < 86400) return `${Math.floor(diff / 3600)}h ago`;
  return new Date(isoString).toLocaleDateString();
}