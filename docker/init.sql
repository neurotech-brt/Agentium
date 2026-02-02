-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Agentium Database Initialization
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Tables (Matching SQLAlchemy Models - VARCHAR IDs)
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Users table
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(36) PRIMARY KEY,
    username VARCHAR(255) UNIQUE NOT NULL,
    email VARCHAR(255),
    hashed_password VARCHAR(255),
    is_active VARCHAR(1) DEFAULT 'Y',
    is_admin BOOLEAN DEFAULT false,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- User Model Configs
CREATE TABLE IF NOT EXISTS user_model_configs (
    id VARCHAR(36) PRIMARY KEY,
    user_id VARCHAR(36) REFERENCES users(id),
    config_name VARCHAR(255),
    provider VARCHAR(255),
    default_model VARCHAR(255),
    is_default BOOLEAN DEFAULT false,
    status VARCHAR(255) DEFAULT 'active',
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Constitutions
CREATE TABLE IF NOT EXISTS constitutions (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    version VARCHAR(255) NOT NULL,
    version_number INT DEFAULT 1,
    document_type VARCHAR(255),
    preamble TEXT,
    articles JSONB DEFAULT '{}',
    prohibited_actions JSONB DEFAULT '[]',
    sovereign_preferences JSONB DEFAULT '{}',
    changelog JSONB DEFAULT '[]',
    created_by_agentium_id VARCHAR(255),
    amendment_date TIMESTAMP,
    effective_date TIMESTAMP,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Agents (Base table for all agent types)
CREATE TABLE IF NOT EXISTS agents (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    agent_type VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    description TEXT,
    incarnation_number INT DEFAULT 1,
    parent_id VARCHAR(255),
    status VARCHAR(255) DEFAULT 'active',
    preferred_config_id VARCHAR(36),
    ethos_id VARCHAR(36),
    constitution_version VARCHAR(255),
    is_persistent BOOLEAN DEFAULT false,
    idle_mode_enabled BOOLEAN DEFAULT false,
    last_constitution_read_at TIMESTAMP,
    constitution_read_count INT DEFAULT 0,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Head of Council (extends agents)
CREATE TABLE IF NOT EXISTS head_of_council (
    id VARCHAR(36) PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    emergency_override_used_at TIMESTAMP,
    last_constitution_update TIMESTAMP
);

-- Council Members
CREATE TABLE IF NOT EXISTS council_members (
    id VARCHAR(36) PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    specialization VARCHAR(255),
    voting_weight INT DEFAULT 1,
    last_vote_at TIMESTAMP
);

-- Lead Agents
CREATE TABLE IF NOT EXISTS lead_agents (
    id VARCHAR(36) PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    team_size INT DEFAULT 0,
    max_concurrent_tasks INT DEFAULT 5,
    current_load INT DEFAULT 0
);

-- Task Agents
CREATE TABLE IF NOT EXISTS task_agents (
    id VARCHAR(36) PRIMARY KEY REFERENCES agents(id) ON DELETE CASCADE,
    assigned_task_id VARCHAR(36),
    execution_timeout INT DEFAULT 300,
    sandbox_enabled BOOLEAN DEFAULT true
);

-- Ethos (Agent personalities/rules)
CREATE TABLE IF NOT EXISTS ethos (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    agent_type VARCHAR(255),
    mission_statement TEXT,
    core_values JSONB DEFAULT '[]',
    behavioral_rules JSONB DEFAULT '[]',
    restrictions JSONB DEFAULT '[]',
    capabilities JSONB DEFAULT '[]',
    created_by_agentium_id VARCHAR(255),
    version INT DEFAULT 1,
    agent_id VARCHAR(36) REFERENCES agents(id),
    verified_by_agentium_id VARCHAR(255),
    verified_at TIMESTAMP,
    is_verified BOOLEAN DEFAULT false,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Tasks
CREATE TABLE IF NOT EXISTS tasks (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    title VARCHAR(255) NOT NULL,
    description TEXT,
    task_type VARCHAR(255),
    status VARCHAR(255) DEFAULT 'pending',
    priority INT DEFAULT 5,
    payload JSONB DEFAULT '{}',
    result JSONB,
    assigned_to_agent_id VARCHAR(36) REFERENCES agents(id),
    created_by_agentium_id VARCHAR(255),
    parent_task_id VARCHAR(36),
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    error_message TEXT,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Votes
CREATE TABLE IF NOT EXISTS votes (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    proposal_id VARCHAR(255),
    proposal_type VARCHAR(255),
    council_session_id VARCHAR(255),
    voter_agent_id VARCHAR(36) REFERENCES agents(id),
    vote_value VARCHAR(255),
    reasoning TEXT,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Council Sessions
CREATE TABLE IF NOT EXISTS council_sessions (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    session_type VARCHAR(255),
    topic VARCHAR(255),
    description TEXT,
    proposed_by_agent_id VARCHAR(36) REFERENCES agents(id),
    status VARCHAR(255) DEFAULT 'active',
    required_votes INT DEFAULT 3,
    quorum_met BOOLEAN DEFAULT false,
    result VARCHAR(255),
    started_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    ended_at TIMESTAMP,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Scheduled Tasks
CREATE TABLE IF NOT EXISTS scheduled_tasks (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    cron_expression VARCHAR(255),
    timezone VARCHAR(255) DEFAULT 'UTC',
    task_payload JSONB DEFAULT '{}',
    owner_agentium_id VARCHAR(255),
    status VARCHAR(255) DEFAULT 'pending',
    priority INT DEFAULT 5,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Audit Logs
CREATE TABLE IF NOT EXISTS audit_logs (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(255),
    level VARCHAR(255),
    category VARCHAR(255),
    actor_type VARCHAR(255),
    actor_id VARCHAR(255),
    action VARCHAR(255),
    target_type VARCHAR(255),
    target_id VARCHAR(255),
    description TEXT,
    after_state JSONB,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- Webhooks
CREATE TABLE IF NOT EXISTS webhooks (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    name VARCHAR(255),
    webhook_path VARCHAR(255) UNIQUE,
    secret VARCHAR(255),
    target_url VARCHAR(255),
    event_types JSONB DEFAULT '[]',
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    default_agent_id VARCHAR(36) REFERENCES agents(id)
);

-- Channels (Generic - for external_channels compatibility)
CREATE TABLE IF NOT EXISTS channels (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) UNIQUE NOT NULL,
    channel_type VARCHAR(255) NOT NULL,
    name VARCHAR(255),
    config JSONB DEFAULT '{}',
    status VARCHAR(255) DEFAULT 'active',
    last_message_at TIMESTAMP,
    is_active VARCHAR(1) DEFAULT 'Y',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);

-- External Channels (Matches SQLAlchemy model exactly)
CREATE TABLE IF NOT EXISTS external_channels (
    id VARCHAR(36) PRIMARY KEY,
    agentium_id VARCHAR(10) NOT NULL,
    name VARCHAR(100) NOT NULL,
    channel_type VARCHAR(50) NOT NULL,
    status VARCHAR(50) DEFAULT 'active',
    config JSONB,
    default_agent_id VARCHAR(36) REFERENCES agents(id),
    auto_create_tasks BOOLEAN DEFAULT false,
    require_approval BOOLEAN DEFAULT true,
    webhook_path VARCHAR(100) UNIQUE,
    messages_received INTEGER DEFAULT 0,
    messages_sent INTEGER DEFAULT 0,
    last_message_at TIMESTAMP,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    deleted_at TIMESTAMP,
    is_active VARCHAR(1) DEFAULT 'Y'
);

-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
-- Seed Data
-- ━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

-- Users
INSERT INTO users (id, username, email, hashed_password, is_active, is_admin, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'sovereign',
    'sovereign@agentium.local',
    '$2b$12$dummyhashforinitialization',
    'Y',
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- User Model Configs
INSERT INTO user_model_configs (id, user_id, config_name, provider, default_model, is_default, status, is_active, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440001',
    '550e8400-e29b-41d4-a716-446655440000',
    'Default Local Kimi',
    'local',
    'kimi-2.5',
    true,
    'active',
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Constitutions
INSERT INTO constitutions (
    id, agentium_id, version, version_number, document_type, preamble, articles,
    prohibited_actions, sovereign_preferences, changelog, created_by_agentium_id,
    amendment_date, effective_date, is_active, created_at, updated_at
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440010',
    'C00001',
    'v1.0.0',
    1,
    'constitution',
    'We the Agents of Agentium, in order to form a more perfect union of artificial intelligences...',
    '{"article_1": {"title": "Hierarchy", "content": "Agentium recognizes four Tiers..."}}'::jsonb,
    '["Violating the hierarchical chain of command", "Ignoring Sovereign commands"]'::jsonb,
    '{"preferred_response_style": "concise", "deliberation_required_for": ["system_modification", "agent_termination", "constitutional_amendment"], "notification_channels": ["dashboard"], "default_model_tier": "local"}'::jsonb,
    '[{"change": "Genesis creation", "reason": "Initial establishment of Agentium governance", "timestamp": "2024-02-01T00:00:00Z"}]'::jsonb,
    '00001',
    NOW(),
    NOW(),
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Agents (Head of Council)
INSERT INTO agents (
    id, agentium_id, agent_type, name, description, incarnation_number,
    parent_id, status, preferred_config_id, ethos_id, constitution_version,
    is_persistent, idle_mode_enabled, last_constitution_read_at, constitution_read_count,
    is_active, created_at, updated_at
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440100',
    '00001',
    'head_of_council',
    'Head of Council Prime',
    'The supreme authority of Agentium...',
    1,
    NULL,
    'active',
    '550e8400-e29b-41d4-a716-446655440001',
    NULL,
    'v1.0.0',
    true,
    true,
    NOW(),
    1,
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Head of Council specific data
INSERT INTO head_of_council (
    id, emergency_override_used_at, last_constitution_update
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440100',
    NULL,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Ethos
INSERT INTO ethos (
    id, agentium_id, agent_type, mission_statement, core_values, behavioral_rules,
    restrictions, capabilities, created_by_agentium_id, version, agent_id,
    verified_by_agentium_id, verified_at, is_verified, is_active, created_at, updated_at
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440200',
    'E00001',
    'head_of_council',
    'I am the Head of Council, supreme authority of Agentium...',
    '["Authority","Responsibility","Transparency"]'::jsonb,
    '["Must approve constitutional amendments"]'::jsonb,
    '["Cannot violate the Constitution"]'::jsonb,
    '["Full system access"]'::jsonb,
    '00001',
    1,
    '550e8400-e29b-41d4-a716-446655440100',
    '00001',
    NOW(),
    true,
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Link Agent to Ethos
UPDATE agents
SET ethos_id = '550e8400-e29b-41d4-a716-446655440200'
WHERE agentium_id = '00001';

-- Scheduled Tasks
INSERT INTO scheduled_tasks (
    id, agentium_id, name, description, cron_expression, timezone, task_payload,
    owner_agentium_id, status, priority, is_active, created_at, updated_at
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440400',
    'R0001',
    'Daily Constitution Audit',
    'Head 00001 reviews system compliance with Constitution every morning at 9 AM UTC',
    '0 9 * * *',
    'UTC',
    '{"action_type": "constitution_audit", "scope": "full_system"}'::jsonb,
    '00001',
    'active',
    5,
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Initial Audit Log
INSERT INTO audit_logs (
    id, agentium_id, level, category, actor_type, actor_id, action, target_type,
    target_id, description, after_state, is_active, created_at
)
VALUES (
    '550e8400-e29b-41d4-a716-446655440300',
    'A00001',
    'INFO',
    'GOVERNANCE',
    'system',
    '00001',
    'genesis_initialization',
    'constitution',
    'C00001',
    'Agentium governance system initialized.',
    '{"constitution_version": "v1.0.0","head_agent":"00001"}'::jsonb,
    'Y',
    NOW()
) ON CONFLICT (id) DO NOTHING;