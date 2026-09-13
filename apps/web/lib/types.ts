/**
 * Shared TypeScript types for the RAGLens frontend.
 * These mirror the backend Pydantic schemas.
 */

// ── Common ───────────────────────────────────────────────────────────────────

export type TraceStatus = "success" | "warning" | "error";

export type SpanType =
  | "query"
  | "query_rewrite"
  | "retrieval"
  | "reranking"
  | "context"
  | "prompt"
  | "llm"
  | "response"
  | "custom";

export type DiagnosticSeverity = "info" | "warning" | "error";

export type DiagnosticCategory =
  | "retrieval"
  | "context"
  | "latency"
  | "tokens"
  | "generation";

// ── Project ──────────────────────────────────────────────────────────────────

export interface Project {
  trace_count?: number;
  error_count?: number;
  total_tokens?: number;
  avg_latency_ms?: number;
  last_trace_at?: string | null;
  id: string;
  name: string;
  description: string | null;
  slug: string;
  is_active: boolean;
  capture_query: boolean;
  capture_context: boolean;
  capture_prompt: boolean;
  capture_response: boolean;
  created_at: string;
  updated_at: string;
}

export interface ProjectStats {
  total_tokens: number;
  success_rate: number;
  activity: Array<{ date: string; requests: number; tokens: number }>;
  latency_buckets: Array<{ label: string; count: number }>;
  total_traces: number;
  error_rate: number;
  avg_latency_ms: number;
  avg_tokens: number;
  traces_change_pct: number | null;
}

// ── Trace ─────────────────────────────────────────────────────────────────────

export interface TraceListItem {
  id: string;
  name: string;
  status: TraceStatus;
  duration_ms: number;
  input: { query?: string } | null;
  metrics: TraceMetrics | null;
  metadata: Record<string, unknown> | null;
  started_at: string;
}

export interface Trace extends TraceListItem {
  project_id: string;
  session_id: string | null;
  user_id: string | null;
  output: Record<string, unknown> | null;
  ended_at: string | null;
  spans: Span[];
  diagnostics: Diagnostic[];
}

export interface TraceMetrics {
  input_tokens: number;
  output_tokens: number;
  total_tokens: number;
  estimated_cost: number;
  context_tokens?: number;
  [key: string]: unknown; // allow provider-specific extras
}

// ── Span ──────────────────────────────────────────────────────────────────────

export interface Span {
  id: string;
  trace_id: string;
  parent_span_id: string | null;
  type: SpanType;
  name: string;
  started_at: string;
  ended_at: string | null;
  duration_ms: number;
  status: TraceStatus;
  input: Record<string, unknown> | null;
  output: Record<string, unknown> | null;
  attributes: Record<string, unknown> | null;
  children?: Span[];            // built client-side from flat list
  retrieval_results?: RetrievalResult[]; // populated on full trace detail
}

// ── Retrieval ─────────────────────────────────────────────────────────────────

export interface RetrievalResult {
  id: string;
  span_id: string;
  rank: number;
  chunk_id: string;
  document_id: string;
  document_name: string;
  content: string;
  score: number;
  retrieval_method: string;
  selected: boolean;
  reranked_rank: number | null;
  reranker_score: number | null;
  metadata: Record<string, unknown> | null;
}

// ── Diagnostic ────────────────────────────────────────────────────────────────

export interface Diagnostic {
  id: string;
  trace_id: string;
  span_id: string | null;
  severity: DiagnosticSeverity;
  category: DiagnosticCategory;
  title: string;
  description: string;
  evidence: Record<string, unknown>;
  suggestions: string[];
}

// ── API Key ───────────────────────────────────────────────────────────────────

export interface ApiKey {
  id: string;
  name: string;
  key_prefix: string;
  created_at: string;
  last_used_at: string | null;
  revoked_at: string | null;
}

// ── Pagination ────────────────────────────────────────────────────────────────

export interface PaginatedResponse<T> {
  items: T[];
  total: number;
  page: number;
  page_size: number;
  has_next: boolean;
}

// ── API Error ─────────────────────────────────────────────────────────────────

export interface ApiError {
  error: {
    code: string;
    message: string;
  };
}
