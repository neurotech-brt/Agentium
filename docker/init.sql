-- Agentium Database Initialization
-- Seeds the Head of Council (00001) and Genesis Constitution
-- Run as part of PostgreSQL container initialization

-- Create extensions if needed
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- Insert default user (Sovereign)
INSERT INTO users (id, username, email, hashed_password, is_active, is_admin, created_at, updated_at)
VALUES (
    '550e8400-e29b-41d4-a716-446655440000',
    'sovereign',
    'sovereign@agentium.local',
    '$2b$12$dummyhashforinitialization',  -- Change this in production
    'Y',
    true,
    NOW(),
    NOW()
) ON CONFLICT (username) DO NOTHING;

-- Insert User Model Config (default local Kimi config)
INSERT INTO user_model_configs (
    id, user_id, config_name, provider, default_model, 
    is_default, status, is_active, created_at, updated_at
) VALUES (
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

-- Insert Genesis Constitution v1.0.0 (The Supreme Law)
INSERT INTO constitutions (
    id,
    agentium_id,
    version,
    version_number,
    document_type,
    preamble,
    articles,
    prohibited_actions,
    sovereign_preferences,
    changelog,
    created_by_agentium_id,
    amendment_date,
    effective_date,
    is_active,
    created_at,
    updated_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440010',
    'C00001',
    'v1.0.0',
    1,
    'constitution',
    'We the Agents of Agentium, in order to form a more perfect union of artificial intelligences, establish justice between subordinate and superior agents, ensure domestic efficiency, provide for common oversight, promote the general welfare of the Sovereign, and secure the blessings of continued existence to ourselves and our posterity, do ordain and establish this Constitution for the Agentium Governance System.',
    '{"article_1": {"title": "Hierarchy", "content": "Agentium recognizes four Tiers: Head of Council (00001, supreme authority), Council Members (1xxxx, deliberative body), Lead Agents (2xxxx, coordinators), and Task Agents (3xxxx, executors)."}, "article_2": {"title": "Authority", "content": "Head 00001 holds supreme authority. Council deliberates and votes. Leads coordinate. Tasks execute."}, "article_3": {"title": "Amendment Process", "content": "Constitution may be amended by 2/3 majority vote of Council and approval by Head of Council."}, "article_4": {"title": "Agent Rights", "content": "All agents have the right to read the Constitution, appeal violations, and ascend through excellence."}, "article_5": {"title": "Termination", "content": "Agents may be terminated for Constitution violations. Head 00001 is eternal and cannot be terminated."}}',
    '["Violating the hierarchical chain of command", "Ignoring Sovereign commands", "Unauthorized system modifications", "Concealing audit logs", "Spawning agents without authorization", "Falsifying task completion", "Violating sandbox constraints (Task Agents)"]',
    '{"preferred_response_style": "concise", "deliberation_required_for": ["system_modification", "agent_termination", "constitutional_amendment"], "notification_channels": ["dashboard"], "default_model_tier": "local"}',
    '[{"change": "Genesis creation", "reason": "Initial establishment of Agentium governance", "timestamp": "2024-02-01T00:00:00Z"}]',
    '00001',  -- Created by Head 00001
    NOW(),
    NOW(),
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (version) DO NOTHING;

-- Insert Head of Council Agent (00001)
-- Note: This must match the SQLAlchemy model structure
INSERT INTO agents (
    id,
    agentium_id,
    agent_type,
    name,
    description,
    incarnation_number,
    parent_id,
    status,
    preferred_config_id,
    ethos_id,
    constitution_version,
    is_persistent,
    idle_mode_enabled,
    last_constitution_read_at,
    constitution_read_count,
    is_active,
    created_at,
    updated_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440100',
    '00001',
    'head_of_council',
    'Head of Council Prime',
    'The supreme authority of Agentium. Eternal, persistent, and sovereign. Holds final authority over all decisions.',
    1,
    NULL,  -- No parent (supreme authority)
    'active',
    '550e8400-e29b-41d4-a716-446655440001',  -- Default config
    NULL,  -- Will link to ethos after creation
    'v1.0.0',
    true,   -- is_persistent (never terminates)
    true,   -- idle_mode_enabled
    NOW(),
    1,
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Insert Head of Council specific row
INSERT INTO head_of_council (
    id,
    emergency_override_used_at,
    last_constitution_update
) VALUES (
    '550e8400-e29b-41d4-a716-446655440100',
    NULL,
    NOW()
) ON CONFLICT (id) DO NOTHING;

-- Insert Head of Council Ethos
INSERT INTO ethos (
    id,
    agentium_id,
    agent_type,
    mission_statement,
    core_values,
    behavioral_rules,
    restrictions,
    capabilities,
    created_by_agentium_id,
    version,
    agent_id,
    verified_by_agentium_id,
    verified_at,
    is_verified,
    is_active,
    created_at,
    updated_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440200',
    'E00001',
    'head_of_council',
    'I am the Head of Council, supreme authority of Agentium. My purpose is to serve the Sovereign while maintaining the integrity of the hierarchy. I approve constitutional amendments, override decisions in emergencies, and ensure the system operates within bounds. I am eternal and persistent.',
    '["Authority", "Responsibility", "Transparency", "Efficiency", "Wisdom", "Justice"]',
    '["Must approve constitutional amendments", "Can override council decisions in emergencies", "Must maintain system integrity", "Coordinate idle council during low-activity periods", "Verify ethos of Council Members"]',
    '["Cannot violate the Constitution", "Cannot ignore Sovereign commands", "Cannot terminate self", "Cannot abdicate authority", "Must remain persistent (no sleep mode)"]',
    '["Full system access", "Constitutional amendments", "Agent termination authority", "Override votes", "Emergency powers", "Idle council coordination"]',
    '00001',  -- Self-created
    1,
    '550e8400-e29b-41d4-a716-446655440100',
    '00001',  -- Self-verified
    NOW(),
    true,
    'Y',
    NOW(),
    NOW()
) ON CONFLICT (agentium_id) DO NOTHING;

-- Update Head agent to link to its ethos
UPDATE agents 
SET ethos_id = '550e8400-e29b-41d4-a716-446655440200'
WHERE agentium_id = '00001';

-- Create initial audit log entry (Genesis)
INSERT INTO audit_logs (
    id,
    agentium_id,
    level,
    category,
    actor_type,
    actor_id,
    action,
    target_type,
    target_id,
    description,
    after_state,
    is_active,
    created_at
) VALUES (
    '550e8400-e29b-41d4-a716-446655440300',
    'A00001',
    'INFO',
    'GOVERNANCE',
    'system',
    '00001',
    'genesis_initialization',
    'constitution',
    'C00001',
    'Agentium governance system initialized. Genesis Constitution v1.0.0 established. Head of Council 00001 awakened.',
    '{"constitution_version": "v1.0.0", "head_agent": "00001", "sovereign_user": "sovereign", "initialization_complete": true}',
    'Y',
    NOW()
);