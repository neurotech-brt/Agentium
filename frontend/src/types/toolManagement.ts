/**
 * Tool Management Type Definitions
 * 
 * TypeScript interfaces for all tool management API shapes.
 * These types correspond to the backend models in tool_creation.py
 */

// ═══════════════════════════════════════════════════════════════
// Marketplace Types
// ═══════════════════════════════════════════════════════════════

export interface MarketplaceListing {
    id: string;
    tool_name: string;
    display_name: string;
    category: string;
    tags: string[];
    average_rating: number;
    download_count: number;
    trust_score: number;
    is_active: boolean;
    yanked_at: string | null;
    yank_reason: string | null;
    published_at: string;
    status?: string;
    import_count?: number;
}

export interface ToolStagingRecord {
    id: string;
    tool_name: string;
    status: 'pending_approval' | 'approved' | 'activated' | 'rejected' | 'deprecated' | 'sunset';
    current_version: number;
    deprecated_at: string | null;
    sunset_at: string | null;
    deprecation_reason: string | null;
    replacement_tool_name: string | null;
}

export interface ToolVersionRecord {
    version_number: number;
    version?: number;
    status: string;
    change_summary: string;
    summary?: string;
    proposed_by?: string;
    created_by?: string;
    created_at?: string;
    code_hash?: string;
}

export type VoteChoice = 'for' | 'against' | 'abstain';

export interface MarketplaceBrowseParams {
    category?: string;
    tags?: string;
    search?: string;
    include_remote?: boolean;
    page?: number;
    page_size?: number;
}

export interface MarketplaceResult {
    listings?: MarketplaceListing[];
    tools?: MarketplaceListing[];
    total: number;
    page: number;
    page_size: number;
}

export interface ToolListResponse {
    tools?: ToolItem[];
    [key: string]: unknown;
}

export interface ToolItem {
    tool_name?: string;
    name?: string;
    description?: string;
    status: string;
    version?: number;
    current_version?: number;
    authorized_tiers?: string[];
    deprecated_by?: string;
    sunset_date?: string;
    reason?: string;
    replacement_tool_name?: string;
}

// ═══════════════════════════════════════════════════════════════
// API Request Types
// ═══════════════════════════════════════════════════════════════

export interface PublishListingRequest {
    tool_name: string;
    display_name: string;
    category: string;
    tags: string[];
}

export interface ImportToolResponse {
    staged: boolean;
    staging_id?: string;
    error?: string;
}

export interface FinalizeImportRequest {
    listing_id: string;
    staging_id: string;
}

export interface FinalizeImportResponse {
    finalized: boolean;
    tool_name?: string;
    error?: string;
}

export interface RateToolRequest {
    rating: number;
}

export interface YankListingRequest {
    reason: string;
}

export interface VoteRequest {
    vote: VoteChoice;
}

export interface ProposeToolRequest {
    name: string;
    description: string;
    code: string;
    created_by_agentium_id: string;
    authorized_tiers: string[];
}

export interface ExecuteToolRequest {
    kwargs: Record<string, unknown>;
    task_id?: string;
}

export interface DeprecateRequest {
    reason: string;
    replacement_tool_name?: string;
    sunset_days?: number;
}

export interface ScheduleSunsetRequest {
    sunset_days: number;
}

export interface ExecuteSunsetRequest {
    force?: boolean;
}

export interface RestoreToolRequest {
    reason: string;
}

export interface ProposeUpdateRequest {
    new_code: string;
    change_summary: string;
}

export interface ApproveUpdateRequest {
    pending_version_id: string;
    approved_by_voting_id?: string;
}

export interface RollbackRequest {
    target_version_number: number;
    reason: string;
}

// ═══════════════════════════════════════════════════════════════
// Analytics Types
// ═══════════════════════════════════════════════════════════════

export interface AnalyticsReport {
    total_calls?: number;
    success_rate?: number;
    avg_latency_ms?: number;
    active_tool_count?: number;
    summary?: {
        total_calls?: number;
        success_rate?: string;
        active_tools?: number;
    };
}

export interface ToolStats {
    total_calls: number;
    success_count: number;
    failure_count: number;
    avg_latency_ms?: number;
    unique_agents: number;
}

export interface ErrorRecord {
    tool_name: string;
    error_message?: string;
    error?: string;
    timestamp?: string;
    called_at?: string;
}

export interface ErrorsResponse {
    errors?: ErrorRecord[];
    items?: ErrorRecord[];
}

export interface AgentUsageResponse {
    agentium_id: string;
    tools_used: string[];
    total_calls: number;
    period_days: number;
}

// ═══════════════════════════════════════════════════════════════
// Generic API Response
// ═══════════════════════════════════════════════════════════════

export interface ApiActionResponse {
    success?: boolean;
    proposed?: boolean;
    voted?: boolean;
    executed?: boolean;
    deprecated?: boolean;
    restored?: boolean;
    staged?: boolean;
    finalized?: boolean;
    rated?: boolean;
    yanked?: boolean;
    scheduled?: boolean;
    executed_sunset?: boolean;
    rolled_back?: boolean;
    approved?: boolean;
    updated?: boolean;
    error?: string;
    message?: string;
    [key: string]: unknown;
}