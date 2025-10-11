import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import { api } from "@/lib/api";
import { useAuth } from "./use-auth";
import type { StartServerRequest } from "@/lib/api";
import toast from "react-hot-toast";

const serverKeys = {
  all: ["servers"] as const,
  lists: () => [...serverKeys.all, "list"] as const,
  list: (filters: string) => [...serverKeys.lists(), { filters }] as const,
  details: () => [...serverKeys.all, "detail"] as const,
  detail: (id: string) => [...serverKeys.details(), id] as const,
};

const authKeys = {
  all: ["auth"] as const,
  apiKeys: () => [...authKeys.all, "api-keys"] as const,
  apiKey: (id: number) => [...authKeys.apiKeys(), id] as const,
  scopes: () => [...authKeys.all, "scopes"] as const,
};

// --- Server Queries ---

export const useServers = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: serverKeys.lists(),
    queryFn: () => api.listServers(),
    select: (data) => data || [],
    enabled: isAuthenticated,
  });
};

export const useStartServer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: ({
      name,
      request,
    }: {
      name: string;
      request: StartServerRequest;
    }) => api.startServer(name, request),
    onSuccess: (_, { name }) => {
      // Invalidate and refetch servers
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success(`Server "${name}" started successfully`);
    },
    onError: (error: Error, { name }) => {
      toast.error(`Failed to start server "${name}": ${error.message}`);
    },
  });
};

export const useStopServer = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (name: string) => api.stopServer(name),
    onSuccess: (_, name) => {
      // Invalidate and refetch servers
      queryClient.invalidateQueries({ queryKey: serverKeys.lists() });
      toast.success(`Server "${name}" stopped successfully`);
    },
    onError: (error: Error, name) => {
      toast.error(`Failed to stop server "${name}": ${error.message}`);
    },
  });
};

// --- Auth Queries ---

export const useApiKeys = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: authKeys.apiKeys(),
    queryFn: () => api.getApiKeys(),
    enabled: isAuthenticated,
  });
};

export const useDeleteApiKey = () => {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: (id: number) => api.deleteApiKey(id),
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: authKeys.apiKeys() });
      toast.success("API key deleted successfully");
    },
    onError: (error: Error) => {
      toast.error(`Failed to delete API key: ${error.message}`);
    },
  });
};

// Export useGlobalConfig
export const useGlobalConfig = () => {
  const { isAuthenticated } = useAuth();
  return useQuery({
    queryKey: ["globalConfig"],
    queryFn: () => api.getGlobalConfig(),
    enabled: isAuthenticated,
  });
};

// Re-export system queries from the new hook
export * from "./use-system-query";
