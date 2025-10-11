"use client";

import { useMemo } from "react";
import { MainLayout } from "@/components/layout/main-layout";
import { StatsGrid } from "@/components/common/stats-grid";
import { ServerCard } from "@/components/common/server-card";
import { Button } from "@/components/ui/button";
import { HealthStatusIcon } from "@/components/common/health-status-icon";
import { getHealthBadgeVariant } from "@/lib/status";
import { formatUptime } from "@/lib/formatters";
import {
  Card,
  CardContent,
  CardDescription,
  CardHeader,
  CardTitle,
} from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import {
  useServers,
  useSystemStatus,
  useSystemHealth,
  useStartServer,
  useStopServer,
} from "@/hooks/use-api-queries";
import type { ServerWithStatus } from "@/types";
import type { SystemStatus, HealthCheck } from "@/lib/api";
import { RefreshCw } from "lucide-react";
import { EasyMcpIcon } from "@/components/common/easymcp-icon";
import Link from "next/link";
import {
  LoadingCard,
  LoadingSpinner,
} from "@/components/common/loading-spinner";
import { useRouter } from "next/navigation";
import { RequireAuth } from "@/components/auth/require-auth";

export default function Home() {
  const router = useRouter();
  const { data: servers = [], isLoading: serversLoading } = useServers();
  const { data: status, isLoading: systemStatusLoading } =
    useSystemStatus() as { data: SystemStatus | undefined; isLoading: boolean };
  const { data: health, isLoading: systemHealthLoading } =
    useSystemHealth() as { data: HealthCheck | undefined; isLoading: boolean };
  const startServer = useStartServer();
  const stopServer = useStopServer();

  const runningServers = useMemo(
    () => servers.filter((s) => s.status?.state === "running"),
    [servers]
  );

  const displayedServers = useMemo(
    () => runningServers.slice(0, 4),
    [runningServers]
  );

  const handleEditServer = (server: ServerWithStatus) => {
    router.push(`/app/servers?edit=${encodeURIComponent(server.name)}`);
  };

  const systemLoading = systemStatusLoading || systemHealthLoading;

  return (
    <RequireAuth>
      <MainLayout>
        <div className="space-y-8">
          {/* Header */}
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold">Dashboard</h1>
              <p className="text-muted-foreground mt-2">
                Monitor and manage your MCP servers
              </p>
            </div>
          </div>

          {/* Stats Grid */}
          <StatsGrid />

          {/* Main Content Grid */}
          <div className="grid grid-cols-1 gap-6 lg:grid-cols-3">
            {/* Active Servers Section */}
            <div className="space-y-4 lg:col-span-2">
              <div className="flex items-center justify-between">
                <h2 className="text-xl font-semibold">Active Servers</h2>
                <Button variant="ghost" size="sm" asChild>
                  <Link href="/app/servers">View All</Link>
                </Button>
              </div>

              {serversLoading ? (
                <LoadingCard title="Loading Servers..." />
              ) : displayedServers.length > 0 ? (
                <div className="grid grid-cols-1 gap-4 md:grid-cols-2">
                  {displayedServers.map((server) => (
                    <ServerCard
                      key={server.name}
                      server={server}
                      onStart={(name) =>
                        startServer.mutate({ name, request: {} })
                      }
                      onStop={stopServer.mutate}
                      onEdit={handleEditServer}
                    />
                  ))}
                </div>
              ) : (
                <Card>
                  <CardContent className="p-8 text-center">
                    <EasyMcpIcon className="text-muted-foreground mx-auto mb-4 h-12 w-12" />
                    <h3 className="mb-2 text-lg font-semibold">
                      No Active Servers
                    </h3>
                    <p className="text-muted-foreground mb-4">
                      Get started by adding your first MCP server
                    </p>
                    <Button asChild>
                      <Link href="/app/servers">Add Server</Link>
                    </Button>
                  </CardContent>
                </Card>
              )}
            </div>

            {/* System Status & Activity */}
            <div className="space-y-4">
              {/* System Health */}
              <Card>
                <CardHeader>
                  <CardTitle className="flex items-center text-base">
                    {systemLoading ? (
                      <RefreshCw className="mr-2 h-4 w-4 animate-spin" />
                    ) : (
                      <HealthStatusIcon status={health?.status || "unknown"} />
                    )}
                    System Health
                  </CardTitle>
                  <CardDescription>
                    Overall system status and health checks
                  </CardDescription>
                </CardHeader>
                <CardContent>
                  {systemLoading ? (
                    <div className="flex justify-center p-4">
                      <LoadingSpinner />
                    </div>
                  ) : health ? (
                    <div className="space-y-3">
                      <div className="flex items-center justify-between">
                        <span className="text-sm">Overall Status</span>
                        <Badge variant={getHealthBadgeVariant(health.status)}>
                          {health.status}
                        </Badge>
                      </div>
                      {Object.entries(health.checks).map(
                        ([component, status]) => (
                          <div
                            key={component}
                            className="flex items-center justify-between"
                          >
                            <span className="text-sm capitalize">
                              {component}
                            </span>
                            <Badge variant={getHealthBadgeVariant(status)}>
                              {status}
                            </Badge>
                          </div>
                        )
                      )}
                      {status && (
                        <div className="mt-3 border-t pt-3">
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Uptime</span>
                            <span className="text-sm font-medium">
                              {formatUptime(status.uptime)}
                            </span>
                          </div>
                          <div className="flex items-center justify-between">
                            <span className="text-sm">Version</span>
                            <span className="text-sm font-medium">
                              {status.version}
                            </span>
                          </div>
                        </div>
                      )}
                    </div>
                  ) : (
                    <p className="text-muted-foreground text-center text-sm">
                      No health data
                    </p>
                  )}
                </CardContent>
              </Card>
            </div>
          </div>
        </div>
      </MainLayout>
    </RequireAuth>
  );
}
