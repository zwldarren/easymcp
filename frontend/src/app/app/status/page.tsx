"use client";

import { useQueryClient } from "@tanstack/react-query";
import { MainLayout } from "@/components/layout/main-layout";
import { Button } from "@/components/ui/button";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useSystemStatus,
  useSystemHealth,
  useSystemMetrics,
  useServers,
} from "@/hooks/use-api-queries";
import type { SystemStatus, HealthCheck, SystemMetrics } from "@/lib/api";
import { HealthStatusIcon } from "@/components/common/health-status-icon";
import { getHealthBadgeVariant } from "@/lib/status";
import {
  formatUptime,
  formatPercentage,
  formatTimestamp,
} from "@/lib/formatters";
import {
  RefreshCw,
  Activity,
  Server,
  Clock,
  Zap,
  TrendingUp,
  TrendingDown,
} from "lucide-react";
import { LoadingCard } from "@/components/common/loading-spinner";
import { RequireAuth } from "@/components/auth/require-auth";

export default function StatusPage() {
  const queryClient = useQueryClient();
  const { data: status, isLoading: statusLoading } = useSystemStatus() as {
    data: SystemStatus | undefined;
    isLoading: boolean;
  };
  const { data: health, isLoading: healthLoading } = useSystemHealth() as {
    data: HealthCheck | undefined;
    isLoading: boolean;
  };
  const { data: metrics, isLoading: metricsLoading } = useSystemMetrics() as {
    data: SystemMetrics | undefined;
    isLoading: boolean;
  };
  const { data: servers = [] } = useServers();

  const isLoading = statusLoading || healthLoading || metricsLoading;

  const handleRefresh = () => {
    queryClient.invalidateQueries({ queryKey: ["system"] });
    queryClient.invalidateQueries({ queryKey: ["servers"] });
  };

  const serverStats = {
    total: servers.length,
    running: servers.filter((s) => s.status?.state === "running").length,
    stopped: servers.filter((s) => s.status?.state === "stopped").length,
    error: servers.filter((s) => s.status?.state === "error").length,
  };

  return (
    <RequireAuth>
      <MainLayout>
        <div className="space-y-6">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">System Status</h1>
              <p className="text-muted-foreground mt-2">
                Monitor system health, performance, and server status
              </p>
            </div>
            <div className="flex items-center space-x-4">
              <div className="text-muted-foreground text-sm">
                {status &&
                  `Last updated: ${formatTimestamp(new Date().toISOString())}`}
              </div>
              <Button onClick={handleRefresh} disabled={isLoading}>
                <RefreshCw
                  className={`mr-2 h-4 w-4 ${isLoading ? "animate-spin" : ""}`}
                />
                Refresh
              </Button>
            </div>
          </div>

          {isLoading && <LoadingCard title="Loading System Status..." />}

          {!isLoading && (
            <>
              {/* System Overview */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-base">
                      <HealthStatusIcon status={health?.status || "unknown"} />
                      <span className="ml-2">System Health</span>
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Status</span>
                        <Badge
                          variant={getHealthBadgeVariant(
                            health?.status || "unknown"
                          )}
                        >
                          {health?.status || "Unknown"}
                        </Badge>
                      </div>
                      <div className="text-muted-foreground text-xs">
                        Last check:{" "}
                        {health?.timestamp
                          ? formatTimestamp(health.timestamp)
                          : "Never"}
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-base">
                      <Server className="mr-2 h-4 w-4" />
                      Server Status
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Running</span>
                        <Badge variant="default">{serverStats.running}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Stopped</span>
                        <Badge variant="secondary">{serverStats.stopped}</Badge>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Errors</span>
                        <Badge variant="destructive">{serverStats.error}</Badge>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-base">
                      <Activity className="mr-2 h-4 w-4" />
                      Request Metrics
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Total</span>
                        <span className="font-medium">
                          {metrics?.requests?.total?.toLocaleString() || 0}
                        </span>
                      </div>
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Success Rate</span>
                        <span className="font-medium">
                          {formatPercentage(
                            metrics?.requests?.successful || 0,
                            metrics?.requests?.total || 0
                          )}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader className="pb-3">
                    <CardTitle className="flex items-center text-base">
                      <Clock className="mr-2 h-4 w-4" />
                      System Uptime
                    </CardTitle>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-2">
                      <div className="text-2xl font-bold">
                        {formatUptime(status?.uptime || 0)}
                      </div>
                      <div className="text-muted-foreground text-xs">
                        Since{" "}
                        {status?.api_last_activity
                          ? formatTimestamp(status.api_last_activity)
                          : "Unknown"}
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>

              {/* Health Checks */}
              <Card>
                <CardHeader>
                  <CardTitle>Health Checks</CardTitle>
                  <CardDescription>
                    Detailed status of system components
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {health?.checks ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {Object.entries(health.checks).map(
                        ([component, status]) => (
                          <div
                            key={component}
                            className="flex items-center justify-between rounded-lg border p-3"
                          >
                            <div className="flex items-center space-x-3">
                              <HealthStatusIcon status={status} />
                              <span className="font-medium capitalize">
                                {component}
                              </span>
                            </div>
                            <Badge variant={getHealthBadgeVariant(status)}>
                              {status}
                            </Badge>
                          </div>
                        )
                      )}
                    </div>
                  ) : (
                    <div className="text-muted-foreground py-8 text-center">
                      No health check data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Server Instances */}
              <Card>
                <CardHeader>
                  <CardTitle>Server Instances</CardTitle>
                  <CardDescription>
                    Current status of all MCP server instances
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {status?.server_instances &&
                  Object.keys(status.server_instances).length > 0 ? (
                    <div className="grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-3">
                      {Object.entries(status.server_instances).map(
                        ([name, state]) => (
                          <div
                            key={name}
                            className="flex items-center justify-between rounded-lg border p-3"
                          >
                            <div className="flex items-center space-x-3">
                              <div
                                className={`h-3 w-3 rounded-full ${
                                  state === "running"
                                    ? "bg-green-500"
                                    : state === "stopped"
                                      ? "bg-gray-400"
                                      : state === "error"
                                        ? "bg-red-500"
                                        : "bg-yellow-500"
                                }`}
                              />
                              <span className="font-medium">{name}</span>
                            </div>
                            <Badge
                              variant={
                                state === "running"
                                  ? "default"
                                  : state === "stopped"
                                    ? "secondary"
                                    : state === "error"
                                      ? "destructive"
                                      : "outline"
                              }
                            >
                              {state}
                            </Badge>
                          </div>
                        )
                      )}
                    </div>
                  ) : (
                    <div className="text-muted-foreground py-8 text-center">
                      No server instance data available
                    </div>
                  )}
                </CardContent>
              </Card>

              {/* Performance Metrics */}
              <div className="grid grid-cols-1 gap-6 md:grid-cols-2">
                <Card>
                  <CardHeader>
                    <CardTitle>Performance Overview</CardTitle>
                    <CardDescription>
                      Real-time system performance indicators
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-4">
                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Zap className="h-4 w-4" />
                          <span className="text-sm">API Response Time</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">
                            {metrics?.performance?.last_response_time_ms?.toFixed(
                              1
                            ) || "0"}
                            ms
                          </span>
                          <TrendingDown className="h-3 w-3 text-green-500" />
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Activity className="h-4 w-4" />
                          <span className="text-sm">Memory Usage</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">
                            {metrics?.performance?.memory_used_mb?.toFixed(1) ||
                              "0"}
                            MB
                          </span>
                          <TrendingUp className="h-3 w-3 text-red-500" />
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Server className="h-4 w-4" />
                          <span className="text-sm">CPU Usage</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">
                            {metrics?.performance?.cpu_usage_percent?.toFixed(
                              1
                            ) || "0"}
                            %
                          </span>
                          <TrendingDown className="h-3 w-3 text-green-500" />
                        </div>
                      </div>

                      <div className="flex items-center justify-between">
                        <div className="flex items-center space-x-2">
                          <Clock className="h-4 w-4" />
                          <span className="text-sm">Avg Response Time</span>
                        </div>
                        <div className="flex items-center space-x-1">
                          <span className="font-medium">
                            {metrics?.performance?.average_response_time_ms?.toFixed(
                              1
                            ) || "0"}
                            ms
                          </span>
                          <TrendingDown className="h-3 w-3 text-green-500" />
                        </div>
                      </div>
                    </div>
                  </CardContent>
                </Card>

                <Card>
                  <CardHeader>
                    <CardTitle>System Information</CardTitle>
                    <CardDescription>
                      Real-time system details and environment information
                    </CardDescription>
                  </CardHeader>
                  <CardContent>
                    <div className="space-y-3">
                      <div className="flex justify-between">
                        <span className="text-muted-foreground text-sm">
                          Version
                        </span>
                        <span className="text-sm font-medium">
                          {status?.version || "Unknown"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground text-sm">
                          Python
                        </span>
                        <span className="text-sm font-medium">
                          {metrics?.environment?.python_version || "Unknown"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground text-sm">
                          Platform
                        </span>
                        <span className="text-sm font-medium">
                          {metrics?.environment?.platform || "Unknown"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground text-sm">
                          Architecture
                        </span>
                        <span className="text-sm font-medium">
                          {metrics?.environment?.architecture || "Unknown"}
                        </span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-muted-foreground text-sm">
                          Hostname
                        </span>
                        <span className="text-sm font-medium">
                          {metrics?.environment?.hostname || "Unknown"}
                        </span>
                      </div>
                    </div>
                  </CardContent>
                </Card>
              </div>
            </>
          )}
        </div>
      </MainLayout>
    </RequireAuth>
  );
}
