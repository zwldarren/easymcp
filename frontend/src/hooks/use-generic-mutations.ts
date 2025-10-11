import { useMutation, useQueryClient } from "@tanstack/react-query";
import { useEffect, useRef } from "react";
import { api } from "@/lib/api";
import toast from "react-hot-toast";
import type { ServerConfig, GlobalConfig } from "@/lib/api";

/**
 * Generic mutation hook with standardized error handling and success notifications
 */
export function useGenericMutation<TData = unknown, TVariables = unknown>({
  mutationFn,
  successMessage,
  errorMessage,
  onSuccess,
  onError,
  invalidateQueries = [],
}: {
  mutationFn: (variables: TVariables) => Promise<TData>;
  successMessage?: string;
  errorMessage?: string;
  onSuccess?: (data: TData, variables: TVariables) => void;
  onError?: (error: Error, variables: TVariables) => void;
  invalidateQueries?: string[][];
}) {
  const queryClient = useQueryClient();

  return useMutation({
    mutationFn,
    onSuccess: (data, variables) => {
      if (successMessage) {
        toast.success(successMessage);
      }

      // Invalidate specified queries
      invalidateQueries.forEach((queryKey) => {
        queryClient.invalidateQueries({ queryKey });
      });

      onSuccess?.(data, variables);
    },
    onError: (error, variables) => {
      const message = errorMessage || error.message || "Operation failed";
      toast.error(message);
      onError?.(error, variables);
    },
  });
}

/**
 * Optimistic update configuration for mutations
 */
export interface OptimisticUpdateConfig<TData> {
  queryKey: string[];
  updateFn: (oldData: TData[]) => TData[];
  rollbackFn?: (oldData: TData[]) => TData[];
}

/**
 * Hook for optimistic updates - returns functions that work with a specific query client
 */
export function useOptimisticUpdate<TData>(
  config: OptimisticUpdateConfig<TData>
) {
  const queryClient = useQueryClient();

  return {
    onMutate: async () => {
      await queryClient.cancelQueries({ queryKey: config.queryKey });
      const previousData = queryClient.getQueryData<TData[]>(config.queryKey);

      if (previousData) {
        queryClient.setQueryData(
          config.queryKey,
          config.updateFn(previousData)
        );
      }

      return { previousData };
    },
    onError: (
      error: Error,
      variables: unknown,
      context: { previousData?: TData[] }
    ) => {
      if (context?.previousData && config.rollbackFn) {
        queryClient.setQueryData(
          config.queryKey,
          config.rollbackFn(context.previousData)
        );
      }
    },
    onSettled: () => {
      queryClient.invalidateQueries({ queryKey: config.queryKey });
    },
  };
}

/**
 * Hook for polling status updates with proper cleanup
 */
export function useStatusPoller<TItem extends { name: string }>({
  queryKey,
  statusField,
  stopCondition,
  interval = 3000,
  maxDuration = 30000,
}: {
  queryKey: string[];
  statusField: keyof TItem;
  stopCondition: (status: string) => boolean;
  interval?: number;
  maxDuration?: number;
}) {
  const queryClient = useQueryClient();
  const pollIntervals = useRef<Map<string, NodeJS.Timeout>>(new Map());
  const timeoutRefs = useRef<Map<string, NodeJS.Timeout>>(new Map());

  const startPolling = (identifier: string) => {
    // Clear any existing polling for this identifier
    stopPolling(identifier);

    const pollInterval = setInterval(async () => {
      try {
        const currentData = queryClient.getQueryData<TItem[]>(queryKey);
        if (!currentData) return;

        const item = currentData.find((item) => item.name === identifier);
        if (!item) return;

        const status = String(item[statusField]);

        // Stop polling if condition is met
        if (stopCondition(status)) {
          stopPolling(identifier);
          return;
        }

        // Update with new status (this would typically come from an API call)
        // For now, we'll just invalidate to trigger a refetch
        queryClient.invalidateQueries({ queryKey });
      } catch (error) {
        console.error("Error during polling:", error);
        stopPolling(identifier);
      }
    }, interval);

    // Store the interval reference
    pollIntervals.current.set(identifier, pollInterval);

    // Stop polling after max duration
    const timeoutRef = setTimeout(() => {
      stopPolling(identifier);
    }, maxDuration);

    timeoutRefs.current.set(identifier, timeoutRef);
  };

  const stopPolling = (identifier: string) => {
    // Clear the interval if it exists
    const interval = pollIntervals.current.get(identifier);
    if (interval) {
      clearInterval(interval);
      pollIntervals.current.delete(identifier);
    }

    // Clear the timeout if it exists
    const timeout = timeoutRefs.current.get(identifier);
    if (timeout) {
      clearTimeout(timeout);
      timeoutRefs.current.delete(identifier);
    }
  };

  const stopAllPolling = () => {
    // Clear all intervals
    pollIntervals.current.forEach((interval) => clearInterval(interval));
    pollIntervals.current.clear();

    // Clear all timeouts
    timeoutRefs.current.forEach((timeout) => clearTimeout(timeout));
    timeoutRefs.current.clear();
  };

  // Cleanup on unmount
  useEffect(() => {
    return () => {
      stopAllPolling();
    };
  }, []);

  return { startPolling, stopPolling, stopAllPolling };
}

/**
 * Common mutation configurations
 */
export const commonMutations = {
  // Server mutations
  createServer: {
    mutationFn: ({ name, config }: { name: string; config: ServerConfig }) =>
      api.createServer(name, config),
    successMessage: "Server created successfully",
    errorMessage: "Failed to create server",
    invalidateQueries: [["servers", "list"]],
  },

  updateServer: {
    mutationFn: ({ name, config }: { name: string; config: ServerConfig }) =>
      api.updateServerConfig(name, config),
    successMessage: "Server updated successfully",
    errorMessage: "Failed to update server",
    invalidateQueries: [["servers", "list"]],
  },

  deleteServer: {
    mutationFn: (name: string) => api.deleteServerConfig(name),
    successMessage: "Server deleted successfully",
    errorMessage: "Failed to delete server",
    invalidateQueries: [["servers", "list"]],
  },

  // API Key mutations
  createApiKey: {
    mutationFn: (data: { name: string; description?: string }) =>
      api.createApiKey(data),
    successMessage: "API key created successfully",
    errorMessage: "Failed to create API key",
    invalidateQueries: [["auth", "api-keys"]],
  },

  // System mutations
  updateGlobalConfig: {
    mutationFn: (config: GlobalConfig) => api.updateGlobalConfig(config),
    successMessage: "Global configuration updated successfully",
    errorMessage: "Failed to update global configuration",
    invalidateQueries: [["system", "global-config"]],
  },
};
