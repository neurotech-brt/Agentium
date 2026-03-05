# Agentium Implementation Roadmap

**Project:** Agentium — Personal AI Agent Nation  
**Version:** 1.1.0-alpha  
**Architecture:** Dual-Storage (PostgreSQL + ChromaDB) with hierarchical agent orchestration  
**Status:** Phase 11 ✅ Implemented | Phase 12 Next  
_Last Updated: 2026-03-05 · Maintainer: Ashmin Dhungana_

---

## Vision

Build a self-governing AI ecosystem where agents operate under constitutional law, make decisions through democratic voting, and manage their own lifecycle — all while being transparent, auditable, and sovereign.

---

## Progress Overview

| Phase | Name                       | Status      |
| ----- | -------------------------- | ----------- |
| 0     | Foundation Infrastructure  | ✅ Complete |
| 1     | Knowledge Infrastructure   | ✅ Complete |
| 2     | Governance Core            | ✅ Complete |
| 3     | Agent Lifecycle Management | ✅ Complete |
| 4     | Multi-Channel Integration  | ✅ Complete |
| 5     | AI Model Integration       | ✅ Complete |
| 6     | Advanced Features          | ✅ Complete |
| 7     | Frontend Development       | ✅ Complete |
| 8     | Testing & Reliability      | ✅ Complete |
| 9     | Production Readiness       | ✅ Complete |
| 10    | Advanced Intelligence      | ✅ Complete |
| 11    | Ecosystem Expansion        | 🚧 90%      |
| 12    | SDK & External Interface   | 🔮 Future   |

---

## Phase 0: Foundation Infrastructure ✅

**Goal:** Rock-solid database and containerization foundation.

### Database

- [x] PostgreSQL 15 with proper schemas
- [x] Agent hierarchy models (0xxxx / 1xxxx / 2xxxx / 3xxxx)
- [x] Foreign key constraints enforcing parent-child relationships
- [x] Indexes on `agent_type`, `status`, `agentium_id`
- [x] Constitution model with version control
- [x] Alembic migrations
- [x] Voting entity models with vote tallying
- [x] Audit log system with immutable records

### Containerization

- [x] Docker Compose orchestration
- [x] PostgreSQL, Redis, ChromaDB services with persistent volumes
- [x] Health checks and network isolation for all services

### Core Entity Models

- [x] `backend/models/entities/agents.py` — Full hierarchy support
- [x] `backend/models/entities/constitution.py` — Versioning
- [x] `backend/models/entities/voting.py` — Democratic mechanics
- [x] `backend/models/entities/audit.py` — Immutable logging
- [x] `backend/models/entities/user.py` — Multi-user RBAC
- [x] `backend/models/entities/base.py` — Common patterns

---

## Phase 1: Knowledge Infrastructure ✅

**Goal:** Dual-storage where structured data lives in PostgreSQL and collective knowledge in ChromaDB.

### Vector Store — `backend/core/vector_store.py`

- [x] ChromaDB client with persistent storage
- [x] Embedding model: `all-MiniLM-L6-v2` (384-dimensional)
- [x] Collections: `constitution_articles`, `agent_ethos`, `task_learnings`, `domain_knowledge`
- [x] `store_knowledge()`, `query_similar()`, `update_knowledge()`, `delete_knowledge()`
- [x] Metadata filtering by `agent_id`, `knowledge_type`, `timestamp`

### RAG Pipeline — `backend/services/rag_service.py`

- [x] Query embedding → similarity search → context window construction
- [x] Constitutional context injection into every agent prompt
- [x] Knowledge deduplication (cosine similarity >0.95 → skip)
- [x] Post-task learning: store outcomes as new knowledge
- [x] Top-K retrieval with relevance threshold (0.7 minimum)

---

## Phase 2: Governance Core ✅

**Goal:** Constitutional law enforcement with democratic amendment process.

### Constitutional Guard — `backend/services/constitutional_guard.py`

- [x] Tier 1 (SQL): keyword blacklist, forbidden patterns, agent boundary checks
- [x] Tier 2 (Semantic): LLM-powered grey-area constitutional analysis
- [x] Three verdicts: ALLOW, BLOCK, VOTE_REQUIRED
- [x] Rate limiting: max 100 Tier 2 checks/hour to control LLM costs
- [x] Constitutional cache: frequently-checked rules cached for 5 minutes

### Voting Service — `backend/services/voting_service.py`

- [x] Proposal types: `AMENDMENT`, `AGENT_LIQUIDATION`, `POLICY_CHANGE`, `EMERGENCY`
- [x] Quorum requirements: 51% for policy, 75% for amendments, 90% for emergency
- [x] Vote delegation (A → B → C chains with cycle detection)
- [x] Automatic tally on deadline expiry (Celery task)
- [x] Amendment diff generation (old vs new article text)

### Amendment Service — `backend/services/amendment_service.py`

- [x] Full lifecycle: propose → vote → ratify → archive old version
- [x] Constitutional lineage tracking (parent → child versions)
- [x] Notification to all agents on ratification
- [x] Original Constitution protection (can never be deleted)

---

## Phase 3: Agent Lifecycle Management ✅

**Goal:** Full autonomous agent lifecycle with constitutional oversight.

### Spawn & Terminate — `backend/services/agent_lifecycle.py`

- [x] Pre-spawn constitutional check (is spawning agent authorized?)
- [x] Post-spawn ethos initialization (read Constitution on first boot)
- [x] Pre-task ritual: constitution freshness check, ethos alignment
- [x] Post-task ritual: outcome logging, ethos compression
- [x] Auto-termination: idle >7 days → Council vote → liquidation
- [x] Emergency agent slot: Head can spawn one emergency agent (1xxxx space)

### Agent Orchestrator — `backend/services/agent_orchestrator.py`

- [x] Intent routing with Constitutional Guard pre-check
- [x] Multi-model execution with failover (OpenAI → Anthropic → Groq → Ollama)
- [x] Task queue management with priority levels
- [x] Critic integration: route subtasks through critic agents before completion
- [x] Checkpoint creation at plan, execution, and critique phases

### Monitoring — `backend/services/monitoring_service.py`

- [x] Background tasks: constitutional patrol (5 min), stale task detection (daily), resource rebalancing (hourly), council health check (weekly), critic queue monitor (1 min)
- [x] Alert levels: INFO, WARNING, CRITICAL, EMERGENCY, CRITIC_VETO
- [x] Alert channels: WebSocket, email, webhook, Slack/Discord

---

## Phase 4: Multi-Channel Integration ✅

### Supported Channels

- [x] WhatsApp (bridge container)
- [x] Telegram
- [x] Discord
- [x] Slack
- [x] Direct API (REST + WebSocket)

### Channel Management — `backend/services/channel_service.py`

- [x] Unified message ingestion → agent routing
- [x] Channel-specific rate limiting
- [x] Message persistence and replay
- [x] Outbound formatting per channel type
- [x] Unified Inbox — all channels in one thread view (`UnifiedInbox.tsx`)

---

## Phase 5: AI Model Integration ✅

### Model Router — `backend/services/model_service.py`

- [x] Provider support: OpenAI, Anthropic, Groq, Ollama, any OpenAI-compatible
- [x] Automatic failover on rate limit or timeout
- [x] Per-agent model assignment (Head uses strongest, Task uses fastest)
- [x] Token budget enforcement per agent tier
- [x] Streaming support via WebSocket
- [x] Dynamic model discovery (Ollama URL, OpenAI-compatible URL)
- [x] Provider analytics: cost tracking, latency histograms, error rates
- [x] A/B testing framework for model comparison (`ab_testing.py`)
- [x] Financial burn dashboard: token usage vs limits, 7-day spend history

---

## Phase 6: Advanced Execution Ecosystem ✅

### Tool Creation Service

- [x] Council approval workflow for new tools
- [x] Tool schema validation and sandboxing

### Acceptance Criteria Service

- [x] Machine-validatable task success conditions
- [x] Auto-evaluation on task completion

### Context Ray Tracing — `backend/services/message_bus.py`

- [x] Role-based context visibility (Planners / Executors / Critics / Siblings)
- [x] Sibling isolation: critics cannot see each other's reviews

### Checkpointing & Time-Travel — `backend/services/checkpoint_service.py`

- [x] Phase boundaries: `plan_approved`, `execution_complete`, `critique_passed`, `manual`
- [x] Restore (rewind to any checkpoint)
- [x] Branch (fork execution from checkpoint)
- [x] State inspector with artifact preview (`CheckpointTimeline.tsx`)

### Remote Code Executor

- [x] Sandboxed Docker container
- [x] Raw data / PII never enters agent reasoning context
- [x] Execution records in `RemoteExecutionRecord` entity

### MCP Server Integration — Phase 6.7

- [x] Constitutional tier-based tool approval (Tier 1 pre-approved / Tier 2 restricted / Tier 3 forbidden)
- [x] Per-invocation audit logging with `agent_id`, timestamp, input hash
- [x] `propose_mcp_server()`, `audit_tool_invocation()`, `get_approved_tools(agent_tier)`, `revoke_mcp_tool()`
- [x] Frontend: `ToolRegistry.tsx` — browse, filter, propose, view invocation logs
- [x] Tier 3 blocked before reaching MCP client
- [ ] Real-time usage stats; revoked tools unavailable in <1s

---

## Phase 7: Frontend Development ✅

### Pages

- [x] Login, Signup, Dashboard, Agents, Tasks, Chat, Settings, Monitoring, Constitution, Channels, Models, Voting
- [x] Sovereign Dashboard (system overview, MCP tools, financial burn, skills, marketplace, federation, RBAC, mobile)

### Key Components

- [x] **Agent Tree** (`AgentTree.tsx`) — collapsible hierarchy, real-time status, color coding by type, spawn/terminate modals
- [x] **Voting Interface** (`VotingPage.tsx`) — active votes with countdowns, amendment diff viewer, real-time tally, delegation, history
- [x] **Constitution Editor** (`ConstitutionPage.tsx`) — article navigation, amendment highlighting, semantic search, diff editor, PDF export
- [x] **Critic Dashboard** (`TasksPage.tsx` → CriticsTab) — per-critic stats, review panels, retry history, performance metrics
- [x] **Checkpoint Timeline** (`CheckpointTimeline.tsx`) — visual phases, restore/branch from checkpoint, state inspector
- [x] **Financial Burn Dashboard** (`FinancialBurnDashboard.tsx`) — token usage vs limits, provider breakdown, 7-day spend history
- [x] **Voice Indicator** (`VoiceIndicator.tsx`) — real-time voice activity with WebSocket streaming
- [x] **Unified Inbox** (`UnifiedInbox.tsx`) — all channels in one thread view

### Pending

- [ ] Drag-and-drop agent reassignment
- [ ] Checkpoint diff view (compare branches)
- [ ] Channel health monitoring and message logs
- [ ] Channel-specific settings (rate limits, filters)

---

## Phase 8: Testing & Reliability ✅

### Functional Tests

- [x] Concurrent agent spawning (1,000 simultaneous)
- [x] 10,000 messages routed without loss
- [x] Message persistence after container restart
- [x] Rate limit enforcement under load
- [x] Hierarchical validation (reject Task → Council direct message)
- [x] Quorum calculation accuracy (1, 5, 100 Council members)
- [x] Concurrent voting sessions
- [x] Vote delegation chain (A → B → C)
- [x] Blacklist enforcement (block `rm -rf /`)
- [x] Semantic violation detection (grey area cases)
- [x] Cache invalidation on constitution update

### Performance Targets

- [x] Constitutional check <50ms (SQL), <200ms (semantic)
- [x] Message routing <100ms
- [x] API response <500ms (p95)
- [x] WebSocket event delivery <50ms
- [x] 100 concurrent dashboard users
- [x] 1,000 tasks/hour throughput

### Reliability Targets

- [x] 87.8% error catch rate via critic layer
- [x] 92.1% overall task success rate
- [x] <7.9% residual errors requiring human intervention
- [x] Zero data loss on container restart
- [x] Graceful degradation when Vector DB unavailable

---

## Phase 9: Production Readiness ✅

### Monitoring — `backend/services/monitoring_service.py`

- [x] Background tasks: constitutional patrol (5 min), stale task detection (daily), resource rebalancing (hourly), council health check (weekly), critic queue monitor (1 min)
- [x] Alert levels: INFO, WARNING, CRITICAL, EMERGENCY, CRITIC_VETO
- [x] Alert channels: WebSocket, email, webhook, Slack/Discord

### Memory & Data Management

- [x] Audit logs: 90-day hot retention, then archive
- [x] Constitution: keep last 10 versions; original never deleted
- [x] Vector DB: weekly reindex, duplicate cleanup
- [x] Tasks/messages: cold storage after 30 days
- [x] Chat retention: last 50 messages always kept; older than 7 days removed
- [ ] Query optimization (slow query log)
- [ ] Connection pool tuning

### Backup & Recovery

- [x] PostgreSQL: daily full backup (7-day rotation)
- [x] Vector DB: weekly snapshot (4-week rotation)
- [x] Agent state restoration from checkpoints
- [x] Point-in-time recovery (last 30 days)
- [ ] Git versioning for config files

### Security

- [x] JWT authentication with configurable token rotation
- [x] RBAC: Sovereign, Council, Lead, Task
- [x] Rate limiting per IP
- [x] Input sanitization (XSS pattern stripping)
- [x] HTTPS enforcement (Nginx + Let's Encrypt via selfhost guide)
- [x] MFA support (token rotation, session management)
- [ ] Audit trail for privilege escalations
- [ ] DDoS hardening at application layer

### Infrastructure

- [x] Kubernetes manifests (`k8s/` directory, Helm charts)
- [x] Prometheus + Grafana monitoring
- [x] CI/CD pipeline (GitHub Actions → GHCR → multi-platform `amd64`/`arm64`)
- [x] Docker Compose for local dev + single-server production

### Access Control

- **Admin users:** full system access, view all tasks
- **Standard users:** view and interact with own tasks only

### Agent Emergency Protocol

- If all agents occupied: Head initiates optimization, terminates idle agents
- If no agents available: Head may create one temporary emergency agent (1xxxx ID space), terminated after task completion
- **Only one active Head of Council at any time**

---

## Phase 10: Advanced Intelligence ✅

### 10.1 Browser Control — `backend/api/routes/browser.py`

- [x] Research, form filling, price monitoring, social posting, e-commerce
- [x] Playwright (headless Chromium) sandboxed execution
- [x] URL whitelist/blacklist, SSRF prevention, content filtering
- [x] Screenshot audit logging
- [ ] Per-session memory / cookie isolation hardening
- [ ] Frontend browser-task UI (live screenshot stream)

### 10.2 Advanced RAG

- [x] Source attribution and confidence scoring per fact
- [x] Contradiction detection across sources
- [x] Automatic fact-checking against Vector DB
- [ ] Cross-document citation graph
- [ ] Confidence decay on stale knowledge entries

### 10.3 Voice Interface — `backend/api/routes/audio.py`

- [x] Speech-to-text: OpenAI Whisper
- [x] Text-to-speech: OpenAI TTS
- [x] WebSocket streaming (real-time voice → agent → voice)
- [x] Voice bridge (`voice-bridge/`) — local STT/TTS support
- [ ] Speaker identification (multi-user voice sessions)
- [ ] Voice channels: phone (Twilio), Discord voice

### 10.4 Autonomous Learning — `backend/services/monitoring_service.py`

- [x] Task outcome analysis (what worked, what failed)
- [x] Best-practice extraction from critic-approved successes
- [x] Anti-pattern detection from critic rejections
- [x] Knowledge consolidation (merge similar learnings, daily background task)
- [ ] Learning decay — reduce weight of outdated patterns
- [ ] Cross-agent learning sharing (federated knowledge pool)

---

## Phase 11: Ecosystem Expansion 🚧

### 11.1 Multi-User RBAC ✅

- [x] DB schema: `users.role` column (`primary_sovereign`, `deputy_sovereign`, `observer`)
- [x] `users.delegated_by_id`, `users.role_expires_at` — time-limited delegation
- [x] `backend/api/routes/capability_routes.py` — capability management API
- [x] Frontend: `RBACManagement.tsx` — full role and delegation UI
- [x] Frontend service: `rbac.ts`
- [ ] End-to-end delegation flow testing (grant → expiry → revocation)
- [ ] Observer read-only enforcement on all write endpoints

### 11.2 Federation ✅

- [x] DB tables: `federated_instances`, `federated_tasks`, `federated_votes` (migration 005)
- [x] `backend/api/routes/federation.py` — federation management API
- [x] Frontend: `FederationPage.tsx` — peer instances, cross-instance task delegation
- [x] Frontend service: `federation.ts`
- [ ] Cross-instance authentication (signed JWT exchange)
- [ ] Federated knowledge sync (pull constitution excerpts from peers)
- [ ] Federated voting on shared governance proposals
- [ ] End-to-end federation testing (two live Agentium instances)

### 11.3 Plugin Marketplace ✅

- [x] DB tables: `plugins`, `plugin_installations`, `plugin_reviews` (migration 005)
- [x] `backend/api/routes/plugins.py` — plugin CRUD, install, review API
- [x] Frontend: `ToolMarketplacePage.tsx` — browse, publish, install, rate plugins
- [x] Frontend service: `plugins.ts`
- [x] Plugin types: channels, specialized critics, AI providers, knowledge sources
- [ ] Plugin verification workflow (Council approval before `is_verified = true`)
- [ ] Sandboxed plugin execution (prevent plugin escaping to host)
- [ ] Revenue share ledger and payment integration

### 11.4 Mobile Apps ✅

- [x] DB tables: `device_tokens`, `notification_preferences` (migration 006)
- [x] `backend/api/routes/mobile.py` — device registration, push notification API
- [x] Frontend: `MobilePage.tsx` — device management, notification preferences
- [ ] iOS native app (Swift)
- [ ] Android native app (Kotlin)
- [ ] Offline mode: cached constitution + task queue sync on reconnect
- [ ] Push notification delivery (FCM/APNs integration)
- [ ] Voice commands from mobile

### 11.5 Scalability (50K → 50M+ agents)

- [x] Expanded agent ID length support in migration 005
- [x] Horizontal scalability readiness (Kubernetes manifests)
- [ ] Frontend rendering optimization for large-scale agent hierarchies (virtual list / pagination)
- [ ] Distributed ChromaDB sharding strategy
- [ ] Agent hierarchy partitioning across multiple PostgreSQL nodes

---

## Phase 12: SDK & External Interface 🔮

**Philosophy:** External callers get the full power of Agentium, but never bypass the Constitution.

### 12.1 REST SDK

- [ ] Python SDK: `pip install agentium-sdk`
  - [ ] `AgentiumClient`, `Task`, `Agent`, `Constitution` classes
  - [ ] Async-first with `asyncio` support
- [ ] TypeScript SDK: `npm install @agentium/sdk`
  - [ ] Full type safety, auto-generated from OpenAPI spec
- [ ] All SDK calls produce identical audit trails to direct API calls

### 12.2 Webhook System

- [ ] Outbound webhooks for task events, votes, constitutional changes
- [ ] HMAC signature verification
- [ ] Retry with exponential backoff
- [ ] Webhook management UI

### 12.3 OpenAPI / Developer Portal

- [ ] Fully annotated OpenAPI 3.1 spec (currently available at `/docs`)
- [ ] Interactive developer portal (Redoc or Stoplight)
- [ ] Code sample generation (curl, Python, TypeScript)

---

## 🧭 What's Left — Priority Queue

### 🔴 High Priority (Phase 11 completion)

1. Observer read-only enforcement on all write API endpoints
2. End-to-end RBAC delegation flow (grant → expiry → auto-revocation)
3. Plugin verification Council-approval workflow
4. Cross-instance federation authentication (signed JWT exchange)
5. Push notification delivery via FCM/APNs

### 🟡 Medium Priority (Polish & Hardening)

6. Browser task frontend UI (live screenshot stream)
7. Speaker identification for multi-user voice sessions
8. Frontend virtual list for large agent hierarchies
9. Checkpoint diff view (compare branches) — Phase 7 pending
10. Channel health monitoring and message logs — Phase 7 pending
11. Drag-and-drop agent reassignment — Phase 7 pending
12. Audit trail for privilege escalations — Phase 9 pending

### 🟢 Low Priority (Future Enhancement)

13. Learning decay on outdated knowledge patterns
14. Git versioning for config files
15. Connection pool tuning and slow query logging
16. Cross-document citation graph in RAG
17. DDoS hardening at application layer

---

## Infrastructure Stack

```
ChromaDB   — Vector Storage  (port 8001)
Redis      — Message Bus + Cache  (port 6379)
PostgreSQL — Entity Storage  (port 5432)
Celery     — Background Tasks
FastAPI    — API Gateway  (port 8000)
React      — Frontend  (port 3000)
Docker     — Remote Executor (sandboxed)
Playwright — Browser Control
Whisper    — Speech-to-Text
OpenAI TTS — Text-to-Speech
```

---

## Known Issues & Technical Debt

**High Priority**

- [ ] Observer read-only enforcement not yet applied to write endpoints
- [ ] Plugin sandboxed execution not yet implemented
- [ ] Federation cross-instance JWT authentication not implemented
- [ ] FCM/APNs push notification delivery not wired up

**Medium Priority**

- [ ] WebSocket reconnection logic needs improvement
- [ ] Frontend error boundaries incomplete
- [ ] Checkpoint diff view (branch comparison) not built
- [ ] Browser task live screenshot UI not built

**Low Priority**

- [ ] UI polish (animations, transitions, dark mode consistency)
- [ ] Mobile responsiveness for complex pages
- [ ] Accessibility (ARIA labels, keyboard navigation)
- [ ] Query optimization (slow query log)
- [ ] Connection pool tuning

---

## Changelog

### v1.1.0-alpha _(current)_

- ✅ Phase 8: Full stress testing, reliability targets hit (87.8% critic catch rate, zero data loss)
- ✅ Phase 9: Kubernetes, Prometheus/Grafana, CI/CD pipeline, MFA, HTTPS
- ✅ Phase 10: Browser automation (Playwright), Advanced RAG, Voice interface (Whisper + TTS), Autonomous learning
- 🚧 Phase 11: Multi-User RBAC, Federation, Plugin Marketplace, Mobile API — all implemented, pending full testing

### v0.7.0-alpha

- ✅ Knowledge Infrastructure (Vector DB + RAG)
- ✅ Initialization Protocol with democratic country naming
- ✅ Tool Creation Service with approval workflow
- ✅ Multi-channel integration (WhatsApp, Telegram)
- ✅ Agent Orchestrator with constitutional context injection
- ✅ Constitutional Guard (SQL + Semantic tiers)
- ✅ Voting Service with frontend integration

### v0.1.0-alpha

- ✅ Foundation: PostgreSQL, Redis, Docker Compose
- ✅ Entity models: Agents, Constitution, Voting, Audit
- ✅ Basic frontend: Dashboard, Agent Tree, Task List
- ✅ Multi-provider AI model support
