import { useQuery, UseQueryOptions } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { POLLING_INTERVALS, STALE_TIME } from "@/lib/polling-config";
import { useAuth } from "./use-auth";
import { usePageVisibility } from "./use-visibility";

interface UseSystemQueryOptions
  extends Omit<UseQueryOptions, "queryKey" | "queryFn"> {
  enabled?: boolean;
}

export function useSystemQuery<T>(
  key: string,
  queryFn: () => Promise<T>,
  options: UseSystemQueryOptions = {}
) {
  const { isAuthenticated } = useAuth();
  const isVisible = usePageVisibility();

  const baseInterval =
    POLLING_INTERVALS[key as keyof typeof POLLING_INTERVALS] ||
    POLLING_INTERVALS.SYSTEM_STATUS;

  return useQuery({
    queryKey: ["system", key],
    queryFn,
    refetchInterval: isVisible ? baseInterval : false,
    staleTime: STALE_TIME.SYSTEM_DATA,
    enabled: (options.enabled ?? true) && isAuthenticated,
    ...options,
  });
}

export function useSystemStatus(options?: UseSystemQueryOptions) {
  return useSystemQuery("status", () => api.getSystemStatus(), options);
}

export function useSystemHealth(options?: UseSystemQueryOptions) {
  return useSystemQuery("health", () => api.getHealthStatus(), options);
}

export function useSystemMetrics(options?: UseSystemQueryOptions) {
  return useSystemQuery(
    "metrics",
    () => api.getSystemMetrics(),
    { enabled: true, ...options } // Metrics don't require auth
  );
}

export function useMcpStatistics(options?: UseSystemQueryOptions) {
  const isVisible = usePageVisibility();

  return useSystemQuery("mcp-statistics", () => api.getMcpStatistics(), {
    refetchInterval: isVisible ? POLLING_INTERVALS.MCP_STATISTICS : false,
    staleTime: STALE_TIME.REAL_TIME,
    ...options,
  });
}
