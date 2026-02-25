# 🧠 Agentium — Remaining Implementation Items

> Consolidated list of features that are **not yet implemented** or **partially implemented** across Phases 4–7.

---

# 🚨 High-Priority Missing Features

## 1️⃣ Channel Health Monitoring Dashboard

**Phase 4 + Phase 7**

**Backend:** ✅ Metrics already tracked (`ChannelMetrics`)  
**Frontend:** ❌ Not implemented
Add in channel page metrics.

### Missing:

- Channel success rate
- Failure rate
- Rate limit hits
- Circuit breaker state (OPEN / HALF_OPEN / CLOSED)
- Consecutive failures
- Visual health indicators (green/yellow/red)
- Centralized dashboard widget

---

## 2️⃣ Message Log Per Channel

**Phase 4 + Phase 7**

**Routing:** ✅ Exists  
**Persistence + UI:** ❌ Not implemented

### Missing:

- Per-channel message history viewer
- Filter by:
  - Channel
  - Agent
  - Date range
  - Success / Failure
- Replay failed messages
- Channel-level audit visibility
- Frontend message log viewer

---

## 3️⃣ A/B Model Testing Framework

**Phase 5**

**Status:** ❌ Not implemented

### Missing:

- Execute same task against multiple models
- Compare:
  - Cost
  - Latency
  - Output quality
  - Critic verdicts
- Automatic best-model selection logic
- Historical experiment tracking
- Experiment result storage

---

# ⚠️ Medium Priority (Backend Exists, Frontend Missing)

## 4️⃣ Provider Performance Metrics Dashboard

**Phase 5**

**Backend:** ✅ Logs latency, cost, success/failure  
**Frontend:** ❌ Aggregation + visualization missing

### Missing:

- Aggregated provider comparison
- Cost over time charts
- Success rate per provider
- Average latency visualization
- Model-level breakdown

---

## 5️⃣ Checkpoint Branch Diff View

**Phase 6 + Phase 7**

**Backend:** ✅ `compare_branches()` implemented  
**Frontend:** ❌ Visualization missing

### Missing:

- Side-by-side branch comparison UI
- Result differences highlighting
- Agent state diff visualization
- Artifact comparison
- Change summary view

---

# 🧩 UX / Productivity Enhancements

## 6️⃣ Drag-and-Drop Agent Reassignment

**Phase 7**

**Status:** ❌ Not implemented

### Missing:

- Drag-and-drop in `AgentTree`
- Real-time hierarchy updates
- Capability validation on reassignment
- Optimistic UI updates

---

## 7️⃣ Checkpoint Export / Import

**Phase 7**

**Status:** ❌ Not implemented

### Missing:

- Export checkpoint as JSON
- Import checkpoint from JSON
- Integrity validation before restore
- Conflict resolution handling

### Use Cases:

- Backup
- Migration
- Debugging
- Sharing execution branches

---

# 📄 Documentation Gap

## 8️⃣ Explicit Critic Routing Documentation

**Phase 6**

**Behavior:** ✅ Implemented by design  
**Documentation:** ❌ Missing formal documentation

### Missing:

- Explanation of critic isolation model
- Routing boundaries
- Interaction limitations
- Design rationale for non-democratic routing

---

# 🎯 Final Consolidated Outstanding Work

1. Channel Health Monitoring Dashboard
2. Message Log Per Channel
3. A/B Model Testing Framework
4. Provider Performance Metrics Dashboard
5. Checkpoint Branch Diff View
6. Drag-and-Drop Agent Reassignment
7. Checkpoint Export / Import
8. Critic Routing Documentation

---

# 🧠 System Maturity Status

Agentium has moved beyond core system construction.

Remaining work is focused on:

- Observability & Monitoring
- Experimentation & Optimization
- UX Enhancements
- Documentation clarity

No core architectural deficiencies remain.
