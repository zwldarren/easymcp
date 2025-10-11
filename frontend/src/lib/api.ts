// API Types and Interfaces

export interface ServerConfig {
  transport: TransportConfig;
  enabled: boolean;
  timeout: number;
}

export type TransportConfig =
  | StdioTransportConfig
  | SSETransportConfig
  | StreamableHttpTransportConfig;

export interface StdioTransportConfig {
  type: "stdio";
  command: string;
  args: string[];
  env: Record<string, string>;
}

export interface SSETransportConfig {
  type: "sse";
  url: string;
  headers: Record<string, string>;
}

export interface StreamableHttpTransportConfig {
  type: "streamable-http";
  url: string;
  headers: Record<string, string>;
  authorization?: AuthorizationConfig;
}

export interface AuthorizationConfig {
  grant: ClientCredentialsGrant;
}

export interface ClientCredentialsGrant {
  grant_type: "client_credentials";
  token_url: string;
  clientId: string;
  clientSecret: string;
  scope?: string;
}

export interface ServerStatus {
  id: string;
  name: string;
  state: "running" | "stopped" | "starting" | "stopping" | "error";
  uptime: number;
  last_activity: string;
  error?: string;
  endpoints: Record<string, string>;
  capabilities: Record<string, number>;
}

export interface ServerWithStatus {
  name: string;
  config: ServerConfig;
  status: ServerStatus;
}

export interface ServerListResponse {
  servers: Record<string, ServerWithStatus>;
}

export interface StartServerRequest {
  stateless?: boolean;
  allow_origins?: string[];
  env?: Record<string, string>;
}

export interface SystemStatus {
  version: string;
  uptime: number;
  api_last_activity: string;
  server_instances: Record<string, string>;
}

export interface HealthCheck {
  status: "healthy" | "degraded" | "unhealthy";
  timestamp: string;
  checks: Record<string, "healthy" | "degraded" | "unhealthy">;
}

export type HealthStatus = "healthy" | "degraded" | "unhealthy";

export interface SystemMetrics {
  timestamp: string;
  servers: Record<string, number>;
  requests: Record<string, number>;
  performance: {
    cpu_usage_percent: number;
    memory_used_mb: number;
    memory_usage_percent: number;
    average_response_time_ms: number;
    last_response_time_ms: number;
    uptime_seconds: number;
  };
  environment: {
    python_version: string;
    platform: string;
    platform_release: string;
    architecture: string;
    processor: string;
    environment: string;
    hostname: string;
  };
}

export interface ServerCallCounts {
  tools: number;
  prompts: number;
  resources: number;
}

export interface ServerStatistics {
  name: string;
  status: string;
  call_counts: ServerCallCounts;
  active_connections: number;
  uptime_seconds: number;
  last_activity: string;
}

export interface McpStatistics {
  timestamp: string;
  servers: Record<string, ServerStatistics>;
  total_active_connections: number;
  total_calls: {
    tools: number;
    prompts: number;
    resources: number;
  };
}

export type LogLevel = "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

export interface GlobalConfig {
  stateless: boolean;
  log_level: LogLevel;
  pass_environment: boolean;
  auth: Record<string, unknown>;
}

export interface McpServersConfig {
  mcpServers: Record<string, ServerConfig>;
}

// Authentication API Types
export interface LoginRequest {
  username: string;
  password: string;
}

export interface LoginResponse {
  access_token: string;
  token_type: string;
  expires_in: number;
  user: UserResponse;
}

export interface UserResponse {
  id: number;
  username: string;
  email?: string;
}

export interface ChangePasswordRequest {
  current_password: string;
  new_password: string;
}

// API Key Types
export interface ApiKeyScope {
  READ_SERVERS: "read:servers";
  ACCESS_SERVERS: "access:servers";
}

export interface ApiKeyCreateRequest {
  name: string;
  description?: string;
}

export interface ApiKeyResponse {
  id: number;
  name: string;
  description?: string;
  key_prefix: string;
  key_hash: string;
  scopes: string[];
  is_active: boolean;
  created_at: string;
  last_used: string | null;
}

export interface ApiKeyCreatedResponse extends ApiKeyResponse {
  api_key: string;
  message: string;
}

export interface ApiKeyListResponse {
  api_keys: ApiKeyResponse[];
}

export interface ScopeListResponse {
  scopes: Record<string, string>;
}

interface ApiError {
  detail?: string;
  message?: string;
  code?: string;
  field?: string;
}

interface RetryConfig {
  maxRetries: number;
  retryDelay: number;
  retryStatuses: number[];
}

// API Client
class ApiClient {
  private baseUrl: string;
  private retryConfig: RetryConfig;
  private authToken: string | null = null;
  private apiKey: string | null = null; // New field for API key

  constructor(
    baseUrl: string = "",
    retryConfig: RetryConfig = {
      maxRetries: 3,
      retryDelay: 1000,
      retryStatuses: [408, 429, 500, 502, 503, 504],
    }
  ) {
    this.baseUrl = baseUrl;
    this.retryConfig = retryConfig;
  }

  setAuthToken(token: string | null): void {
    this.authToken = token;
    // Clear API key when setting auth token
    if (token) {
      this.apiKey = null;
    }
  }

  setApiKey(key: string | null): void {
    this.apiKey = key;
    // Clear auth token when setting API key
    if (key) {
      this.authToken = null;
    }
  }

  private async delay(ms: number): Promise<void> {
    return new Promise((resolve) => setTimeout(resolve, ms));
  }

  private async parseErrorResponse(response: Response): Promise<string> {
    try {
      const errorData: ApiError = await response.json();

      // Handle specific error codes with user-friendly messages
      if (response.status === 401) {
        return "Authentication failed. Please log in again.";
      }
      if (response.status === 403) {
        return "Access denied. You don't have permission to perform this action.";
      }

      if (response.status === 500) {
        return "Server error. Please try again later or contact support.";
      }

      if (errorData.detail) {
        return errorData.detail;
      }
      if (errorData.message) {
        return errorData.message;
      }
      if (errorData.code) {
        return `Error ${errorData.code}: ${response.statusText}`;
      }
    } catch {
      // If we can't parse the error response, use user-friendly status text
      if (response.status === 401) {
        return "Authentication failed. Please log in again.";
      }
      if (response.status === 403) {
        return "Access denied. You don't have permission to perform this action.";
      }

      if (response.status === 500) {
        return "Server error. Please try again later.";
      }
    }
    return `API request failed: ${response.statusText} (${response.status})`;
  }

  /**
   * Get error message from unknown error type
   */
  private getErrorMessage(error: unknown): string {
    if (error instanceof Error) {
      return error.message;
    }
    if (typeof error === "string") {
      return error;
    }
    if (error && typeof error === "object" && "message" in error) {
      return String(error.message);
    }
    return "An unexpected error occurred";
  }

  private async request<T>(
    endpoint: string,
    options: RequestInit = {},
    retryCount = 0
  ): Promise<T> {
    const url = `${this.baseUrl}${endpoint}`;

    // Prepare headers with authentication if token is available
    const headers: Record<string, string> = {
      "Content-Type": "application/json",
      ...(options.headers as Record<string, string>),
    };

    // Set authentication header based on available credentials
    if (this.apiKey) {
      // Use x-api-key header for API key authentication
      headers["x-api-key"] = this.apiKey;
    } else if (this.authToken) {
      // Use Authorization header for JWT token authentication
      headers["Authorization"] = `Bearer ${this.authToken}`;
    }

    // Check if this is a non-idempotent operation (POST, PUT, PATCH, DELETE)
    // and should not be retried on 500 errors
    const isNonIdempotent = ["POST", "PUT", "PATCH", "DELETE"].includes(
      options.method || "GET"
    );
    const shouldRetryOnServerError =
      !isNonIdempotent || endpoint !== "/api/auth/api-keys";

    try {
      const response = await fetch(url, {
        ...options,
        headers,
      });

      if (!response.ok) {
        const errorMessage = await this.parseErrorResponse(response);

        // Check if we should retry
        const shouldRetry =
          retryCount < this.retryConfig.maxRetries &&
          this.retryConfig.retryStatuses.includes(response.status) &&
          (response.status !== 500 || shouldRetryOnServerError);

        if (shouldRetry) {
          await this.delay(this.retryConfig.retryDelay * (retryCount + 1));
          return this.request(endpoint, options, retryCount + 1);
        }

        // Handle authentication errors
        if (response.status === 401) {
          if (typeof window !== "undefined" && !window.location.pathname.includes("/login")) {
            window.location.href = "/login";
          }
        }

        throw new Error(errorMessage);
      }

      if (response.status === 204) {
        return null as T;
      }

      return response.json();
    } catch (error) {
      if (error instanceof Error) {
        // Network errors or other fetch failures
        if (retryCount < this.retryConfig.maxRetries) {
          await this.delay(this.retryConfig.retryDelay * (retryCount + 1));
          return this.request(endpoint, options, retryCount + 1);
        }
        throw error;
      }
      throw new Error(this.getErrorMessage(error));
    }
  }

  // Server management
  async listServers(): Promise<ServerWithStatus[]> {
    const response = await this.request<ServerListResponse>("/api/servers/");
    if (!response || !response.servers) {
      return [];
    }
    return Object.entries(response.servers).map(([name, serverData]) => ({
      ...serverData,
      name,
    }));
  }

  async createServer(name: string, config: ServerConfig): Promise<void> {
    await this.request(`/api/config/servers/${name}`, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  }

  async updateServerConfig(name: string, config: ServerConfig): Promise<void> {
    await this.request(`/api/config/servers/${name}`, {
      method: "PUT",
      body: JSON.stringify(config),
    });
  }

  async deleteServerConfig(name: string): Promise<void> {
    await this.request(`/api/config/servers/${name}`, {
      method: "DELETE",
    });
  }

  async startServer(
    name: string,
    request: StartServerRequest
  ): Promise<ServerStatus> {
    return this.request<ServerStatus>(`/api/servers/${name}/start`, {
      method: "POST",
      body: JSON.stringify(request),
    });
  }

  async stopServer(name: string): Promise<ServerStatus> {
    return this.request<ServerStatus>(`/api/servers/${name}/stop`, {
      method: "POST",
    });
  }

  async getServerStatus(name: string): Promise<ServerStatus> {
    return this.request<ServerStatus>(`/api/servers/${name}/status`);
  }

  // System management
  async getSystemStatus(): Promise<SystemStatus> {
    return this.request<SystemStatus>("/api/status/");
  }

  async getHealthStatus(): Promise<HealthCheck> {
    return this.request<HealthCheck>("/api/status/health");
  }

  async getSystemMetrics(): Promise<SystemMetrics> {
    return this.request<SystemMetrics>("/api/status/metrics");
  }

  async getMcpStatistics(): Promise<McpStatistics> {
    return this.request<McpStatistics>("/api/status/mcp-statistics");
  }

  // Configuration management
  async getGlobalConfig(): Promise<GlobalConfig> {
    return this.request<GlobalConfig>("/api/config/global");
  }

  async updateGlobalConfig(config: GlobalConfig): Promise<void> {
    await this.request("/api/config/global", {
      method: "PUT",
      body: JSON.stringify(config),
    });
  }

  // Authentication management
  async login(credentials: LoginRequest): Promise<LoginResponse> {
    const response = await this.request<LoginResponse>("/api/auth/login", {
      method: "POST",
      body: JSON.stringify(credentials),
    });
    return response;
  }

  async logout(): Promise<{ message: string }> {
    return this.request<{ message: string }>("/api/auth/logout", {
      method: "POST",
    });
  }

  async getCurrentUser(): Promise<UserResponse> {
    return this.request<UserResponse>("/api/auth/me");
  }

  async changePassword(
    data: ChangePasswordRequest
  ): Promise<{ message: string }> {
    return this.request<{ message: string }>("/api/auth/change-password", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  // API Key Management
  async createApiKey(
    data: ApiKeyCreateRequest
  ): Promise<ApiKeyCreatedResponse> {
    return this.request<ApiKeyCreatedResponse>("/api/auth/api-keys", {
      method: "POST",
      body: JSON.stringify(data),
    });
  }

  async getApiKeys(): Promise<ApiKeyListResponse> {
    return this.request<ApiKeyListResponse>("/api/auth/api-keys");
  }

  async deleteApiKey(keyId: number): Promise<{ message: string }> {
    return this.request<{ message: string }>(`/api/auth/api-keys/${keyId}`, {
      method: "DELETE",
    });
  }

  async getAvailableScopes(): Promise<ScopeListResponse> {
    return this.request<ScopeListResponse>("/api/auth/api-keys/scopes");
  }
}

// Use relative URLs in production to avoid CORS issues when served from same origin
const getApiBaseUrl = () => {
  if (typeof window !== "undefined") {
    // In browser
    if (
      window.location.hostname === "localhost" ||
      window.location.hostname === "127.0.0.1"
    ) {
      // Development - use the environment variable or default
      return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
    } else {
      // Production - use relative URL to avoid CORS
      return "";
    }
  } else {
    // Server-side - use environment variable
    return process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  }
};

export const api = new ApiClient(getApiBaseUrl());
