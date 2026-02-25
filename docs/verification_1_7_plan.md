# Agentium — Implementation Plan: Strategic Architecture Improvements

> **Date:** 2026-02-25
> **Status:** Pending User Review
> **Scope:** 8 recommended architectural improvements across 4 strategic pillars

---

## ⚠️ User Review Required

### WARNING

Implementing the Critic Consensus Protocol shifts the review stage from a single-veto system to a multi-agent deliberation. This will significantly alter the behavior of `critic_agents.py` and increase the token usage and time required for the "Review" phase since Critics will now converse with each other before returning a final verdict to the executor.

**Are you comfortable with this tradeoff for the sake of better, deadlock-free decisions?**

### NOTE

Which UI framework are you using for the frontend charts? The Burn Rate Dashboard will require charting libraries (e.g., Recharts or Chart.js). Will default to **recharts** if present in `package.json`.

---

## Proposed Changes

### Pillar 1: Architectural Resilience

#### [MODIFY] `backend/services/message_bus.py`
- Add a Dead-Letter Queue (DLQ) mechanism to `consume_stream()`
- If tracking metadata indicates a message failed processing >3 times, automatically route it to a new `agent:dlq:stream`
- Add a new `replay_dlq()` admin utility method

#### [MODIFY] `backend/models/entities/agents.py`
- Modify `read_and_align_constitution()` and `post_task_ritual()`
- Wrap ChromaDB vector_store calls in a resilient try/except
- On failure, fall back to a newly introduced standard constitution text file (`docs/constitution/core.md`) instead of hard failing the agent progression sequence

---

### Pillar 2: Governance & Critic Enhancements

#### [MODIFY] `backend/services/critic_agents.py`

**Critic Consensus:**
- Instead of an immediate REJECT, if one critic rejects while another passes, spawn a temporary "Senior Critic" (tier 7xxxx) prompt to evaluate the conflicting critiques and determine the final consensus verdict

**Case Law Indexing:**
- When a final REJECT goes through, generate an embedding of the failure scenario and task context
- Insert it into a new ChromaDB collection (`critic_case_law`)

#### [MODIFY] `backend/models/entities/task.py`
- Update task planning methods to query the new `critic_case_law` collection via vector_store
- Inject historical failure warnings into the planner's context prompt

---

### Pillar 3: Scalability & Execution

#### [MODIFY] `backend/services/mcp_governance.py`
- Refactor `execute_mcp_tool()` to support an `async_callback` parameter
- For async=True tools, return an immediate `TaskStatus.SUSPENDED` (or similar WAITING state)
- Register the webhook endpoint in the `ChannelManager`

#### [MODIFY] `backend/services/remote_executor/sandbox.py`
- Add `SandboxPoolManager` class
- On startup, spin up `MIN_WARM_CONTAINERS` (default 3) generic `python:3.11-slim` sandboxes holding idle
- `execute_code()` will:
  1. Pop a warm container from the queue
  2. Inject the code
  3. Execute
  4. Destroy it
  5. Trigger an async background task to replenish the warm pool

---

### Pillar 4: Frontend & UX

#### [NEW] `frontend/src/pages/BurnRateDashboard.tsx`
- Build a new dashboard querying `/api/metrics/financial`
- Combine ModelUsageLog cost metrics with Task success/failure rates
- Plot ROI per agent/tier

#### [MODIFY] `frontend/src/components/checkpoints/CheckpointTimeline.tsx`
- Add an "Inspect State" button that opens an interactive time-travel modal
- Build the `TimeTravelDebugger.tsx` component that queries the `/api/checkpoints/{id}/diff` backend endpoint
- Render the exact state of the AgentTree at that moment

---

## Verification Plan

### Automated Tests

| Test | File | Purpose |
|------|------|---------|
| DLQ Routing | `tests/services/test_message_bus.py` | Verify dead-letter queue routing |
| Warm Pool Security | `tests/services/test_remote_executor.py` | Ensure warm-pooling respects sandbox limits |
| Consensus Protocol | `tests/services/test_critic_agents.py` | Validate new consensus resolves deadlocks |

### Manual Verification

| Check | Action |
|-------|--------|
| Sandbox Latency | Propose and execute a dummy code tool via web UI; observe if execution drops from ~3s to <500ms |
| ChromaDB Fallback | Stop ChromaDB docker container and execute a task; verify fallback to local constitution |
| Burn Rate Charts | Navigate to `/dashboard/burn-rate`; verify charts render correctly |
| Time-Travel Modal | Click a checkpoint in timeline; verify modal displays divergent agent states |

---

## Implementation Checklist

- [ ] **P1.1** Add DLQ mechanism to message_bus.py
- [ ] **P1.2** Add replay_dlq() admin utility
- [ ] **P1.3** Add ChromaDB fallback to agents.py
- [ ] **P1.4** Create docs/constitution/core.md fallback file
- [ ] **P2.1** Implement Critic Consensus Protocol
- [ ] **P2.2** Implement Case Law Indexing with ChromaDB
- [ ] **P2.3** Update task.py to query critic_case_law
- [ ] **P3.1** Refactor execute_mcp_tool() for async callbacks
- [ ] **P3.2** Add SandboxPoolManager class
- [ ] **P3.3** Implement warm pool execution
- [ ] **P4.1** Create BurnRateDashboard.tsx page
- [ ] **P4.2** Add TimeTravelDebugger component
- [ ] **P4.3** Add "Inspect State" button to CheckpointTimeline
- [ ] **TEST** Run all automated tests
- [ ] **TEST** Manual verification of all features

---

> End of Implementation Plan
