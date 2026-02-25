# 🧠 Agentium -- Phase-by-Phase File Verification Map (Phase 1 → Phase 7)

> Structured execution checklist for strict implementation verification.

---

# 🟢 PHASE 1 -- Knowledge Infrastructure

## Files To Check

- backend/core/vector_store.py
- backend/services/knowledge_service.py
- backend/services/initialization_service.py
- backend/requirements.txt
- docker-compose.yml

## Verification Checklist

- [ ] ChromaDB initialized correctly
- [ ] Collection separation implemented
- [ ] Metadata filtering working
- [ ] Semantic search integrated
- [ ] Constitution embedded on genesis
- [ ] RAG context injection before model call
- [ ] No hardcoded collection names
- [ ] Healthcheck for ChromaDB container

---

# 🟢 PHASE 2 -- Governance Core

## Files To Check

- backend/services/message_bus.py
- backend/services/agent_orchestrator.py
- backend/core/constitutional_guard.py
- backend/services/persistent_council.py
- backend/models/entities/voting.py
- backend/services/amendment_service.py
- backend/models/entities/critics.py
- backend/services/critic_agents.py
- backend/api/routes/critics.py

## Verification Checklist

- [ ] Hierarchical routing enforced
- [ ] Rate limiting implemented
- [ ] Constitutional guard severity classification
- [ ] Voting quorum logic dynamic
- [ ] Amendment version increment logic
- [ ] Critics veto independent of council
- [ ] Circular vote prevention
- [ ] Audit logs on all governance actions

---

# 🟢 PHASE 3 -- Agent Lifecycle Management

## Files To Check

- backend/services/reincarnation_service.py
- backend/services/idle_governance.py
- backend/services/capability_registry.py
- backend/models/entities/agents.py

## Verification Checklist

- [ ] ID pool enforcement
- [ ] Parent-child validation
- [ ] Idle threshold auto-liquidation
- [ ] Capability revocation on deletion
- [ ] Audit logs for spawn & liquidation

---

# 🟢 PHASE 4 -- Multi-Channel Integration

## Files To Check

- backend/services/channel_manager.py
- backend/services/channels/base.py
- backend/services/channels/slack.py
- backend/services/channels/whatsapp_unified.py
- backend/models/entities/channels.py
- backend/api/routes/channels.py
- backend/api/routes/websocket.py

## Verification Checklist

- [ ] All channel messages routed through message_bus
- [ ] Retry/backoff logic present
- [ ] Event broadcasting working
- [ ] Message normalization consistent
- [ ] Failure handling verified

---

# 🟢 PHASE 5 -- AI Model Integration

## Files To Check

- backend/services/model_provider.py
- backend/services/api_manager.py
- backend/services/universal_model_provider.py
- backend/services/api_key_manager.py
- backend/api/routes/api_keys.py

## Verification Checklist

- [ ] Multi-provider fallback chain
- [ ] Token counting & pruning
- [ ] Circuit breaker states
- [ ] Budget enforcement
- [ ] Key cooldown & recovery logic
- [ ] All keys down notification

---

# 🟢 PHASE 6 -- Advanced Execution Architecture

## Files To Check

- backend/services/tool_creation_service.py
- backend/services/tool_factory.py
- backend/services/tool_versioning.py
- backend/services/tool_deprecation.py
- backend/services/acceptance_criteria.py
- backend/api/schemas/task.py
- backend/api/routes/tasks.py
- backend/services/checkpoint_service.py
- backend/models/entities/checkpoint.py
- backend/services/remote_executor/service.py
- backend/services/remote_executor/executor.py
- backend/services/remote_executor/sandbox.py
- backend/core/security/execution_guard.py
- backend/api/routes/remote_executor.py
- backend/services/mcp_governance.py
- backend/models/entities/mcp_tool.py
- backend/api/routes/mcp_tools.py

## Verification Checklist

- [ ] Deterministic acceptance checks before AI review
- [ ] Sandbox isolation enforced
- [ ] Resource limits applied
- [ ] ExecutionGuard blocking unsafe code
- [ ] MCP tier restrictions enforced
- [ ] Invocation logging with agent_id
- [ ] Revocation disables tool instantly
- [ ] Checkpoint restore validated

---

# 🟢 PHASE 7 -- Frontend

## Files To Check

- frontend/src/pages/Dashboard.tsx
- frontend/src/pages/AgentsPage.tsx
- frontend/src/pages/TasksPage.tsx
- frontend/src/pages/VotingPage.tsx
- frontend/src/pages/ConstitutionPage.tsx
- frontend/src/pages/ChannelsPage.tsx
- frontend/src/pages/ModelsPage.tsx
- frontend/src/pages/MonitoringPage.tsx
- frontend/src/components/agents/AgentTree.tsx
- frontend/src/components/checkpoints/CheckpointTimeline.tsx
- frontend/src/components/mcp/MCPToolRegistry.tsx
- frontend/src/components/common/ErrorBoundary.tsx
- frontend/src/components/GlobalWebSocketProvider.tsx
- frontend/src/services/

## Verification Checklist

- [ ] WebSocket updates wired correctly
- [ ] Voting countdown accurate
- [ ] Amendment diff viewer functional
- [ ] Agent tree reflects backend state
- [ ] MCP usage statistics visible
- [ ] Error boundaries implemented
- [ ] Service layer API integration validated

---

# 🧠 System-Level Final Checks

- [ ] Authentication flow complete
- [ ] Logging system consistent
- [ ] Environment variables validated
- [ ] Production build successful
- [ ] Performance profiling done
- [ ] Security review completed
- [ ] No missing integration points

---

# 🔧 Improvement Review Section

For each phase evaluate:

- [ ] Refactoring opportunities
- [ ] Code duplication removal
- [ ] Performance bottlenecks
- [ ] Security hardening
- [ ] Architectural simplification
- [ ] Improved error handling
- [ ] Test coverage gaps

---

> End of Verification Playbook
