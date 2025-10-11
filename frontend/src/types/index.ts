/**
 * Type definitions for the frontend
 */

// Import specific types we need for the interfaces
import type {
  ServerWithStatus as ApiServerWithStatus,
  SystemStatus as ApiSystemStatus,
  HealthCheck as ApiHealthCheck,
  SystemMetrics as ApiSystemMetrics,
} from "@/lib/api";

// Re-export all types from the API client
export * from "@/lib/api";

// UI-specific types
export interface ActivityLog {
  id: number;
  action: string;
  server: string;
  time: string;
  status: "success" | "warning" | "error";
}

export interface LoadingState {
  isLoading: boolean;
  error: string | null;
}

export interface AppState {
  // Server state
  servers: ApiServerWithStatus[];
  serversLoading: boolean;
  serversError: string | null;
  selectedServer: string | null;

  // System state
  status: ApiSystemStatus | null;
  health: ApiHealthCheck | null;
  metrics: ApiSystemMetrics | null;
  systemLoading: boolean;
  systemError: string | null;
  lastSystemUpdate: number;
}

// Type guards for better runtime type safety
export const isServerRunning = (server: ApiServerWithStatus): boolean => {
  return server.status?.state === "running";
};

export const isServerError = (server: ApiServerWithStatus): boolean => {
  return server.status?.state === "error" || !!server.status?.error;
};

export const isHealthHealthy = (health: ApiHealthCheck): boolean => {
  return health.status === "healthy";
};

export const isHealthDegraded = (health: ApiHealthCheck): boolean => {
  return health.status === "degraded";
};

export const isHealthUnhealthy = (health: ApiHealthCheck): boolean => {
  return health.status === "unhealthy";
};
