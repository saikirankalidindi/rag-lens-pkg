/**
 * TanStack Query hooks for RAGLens data fetching.
 *
 * All hooks are "auth-aware" — they depend on the session being authenticated
 * so they don't fire unauthenticated requests.
 */
import { useQuery } from "@tanstack/react-query";
import { projectsApi, tracesApi, type TraceFilters } from "@/lib/api";
import { useAuth } from "@/lib/auth-context";

// ── Projects ──────────────────────────────────────────────────────────────────

export function useProjects() {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["projects"],
    queryFn: () => projectsApi.list(),
    enabled: isAuthenticated,
  });
}

export function useProject(projectId: string) {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["projects", projectId],
    queryFn: () => projectsApi.get(projectId),
    enabled: isAuthenticated && !!projectId,
  });
}

export function useProjectStats(projectId: string) {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["projects", projectId, "stats"],
    queryFn: () => projectsApi.getStats(projectId),
    enabled: isAuthenticated && !!projectId,
    // Refresh stats every 30 seconds
    refetchInterval: 30_000,
  });
}

// ── Traces ────────────────────────────────────────────────────────────────────

export function useTraces(projectId: string, filters: TraceFilters = {}) {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["projects", projectId, "traces", filters],
    queryFn: () => tracesApi.list(projectId, filters),
    enabled: isAuthenticated && !!projectId,
    // Keep previous data while new page is loading for smooth pagination
    placeholderData: (prev) => prev,
  });
}

export function useTrace(projectId: string, traceId: string) {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["projects", projectId, "traces", traceId],
    queryFn: () => tracesApi.get(projectId, traceId),
    enabled: isAuthenticated && !!projectId && !!traceId,
  });
}
