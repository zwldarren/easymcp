"use client";

import { useMemo, memo } from "react";
import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { TrendingUp, TrendingDown, Activity, Clock, Zap } from "lucide-react";
import { EasyMcpIcon } from "./easymcp-icon";
import {
  useServers,
  useSystemStatus,
  useMcpStatistics,
} from "@/hooks/use-api-queries";
import type { SystemStatus, McpStatistics } from "@/lib/api";
import { formatNumber } from "@/lib/formatters";

interface MetricCardProps {
  title: string;
  value: string | number;
  change?: {
    value: number;
    type: "increase" | "decrease";
  };
  icon: React.ComponentType<{ className?: string }>;
  description?: string;
  className?: string;
}

export const MetricCard = memo(function MetricCard({
  title,
  value,
  change,
  icon: Icon,
  description,
  className,
}: MetricCardProps) {
  return (
    <Card
      className={cn(
        "transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
        className
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <CardTitle className="text-muted-foreground text-sm font-medium">
            {title}
          </CardTitle>
          <div className="icon-container-sm">
            <Icon className="h-4 w-4" />
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <div className="flex items-baseline space-x-2">
          <div className="text-2xl font-bold">{value}</div>
          {change && (
            <div
              className={cn(
                "flex items-center space-x-1 text-xs font-medium",
                change.type === "increase"
                  ? "text-green-600 dark:text-green-500"
                  : "text-red-600 dark:text-red-500"
              )}
            >
              {change.type === "increase" ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span>{Math.abs(change.value)}%</span>
            </div>
          )}
        </div>

        {description && (
          <p className="text-muted-foreground mt-2 text-xs">{description}</p>
        )}
      </CardContent>
    </Card>
  );
});

interface StatsGridProps {
  className?: string;
}

export const StatsGrid = memo(function StatsGrid({
  className,
}: StatsGridProps) {
  const { data: servers = [] } = useServers();
  const { data: status } = useSystemStatus() as {
    data: SystemStatus | undefined;
  };
  const { data: mcpStats } = useMcpStatistics() as {
    data: McpStatistics | undefined;
  };

  const stats = useMemo(() => {
    const runningServers = servers.filter(
      (s) => s.status?.state === "running"
    ).length;
    const totalServers = servers.length;
    const stoppedServers = servers.filter(
      (s) => s.status?.state === "stopped"
    ).length;
    const errorServers = servers.filter(
      (s) => s.status?.state === "error"
    ).length;

    const totalCalls = mcpStats?.total_calls
      ? mcpStats.total_calls.tools +
        mcpStats.total_calls.prompts +
        mcpStats.total_calls.resources
      : 0;

    // Calculate total capabilities across all running servers
    const totalCapabilities = servers.reduce((acc, server) => {
      if (server.status?.state === "running" && server.status?.capabilities) {
        const serverCaps = Object.values(server.status.capabilities).reduce(
          (sum, count) => sum + count,
          0
        );
        return acc + serverCaps;
      }
      return acc;
    }, 0);

    const uptime = status?.uptime || 0;
    const uptimeHours = Math.floor(uptime / 3600);
    const uptimeDays = Math.floor(uptimeHours / 24);

    return [
      {
        title: "Total Servers",
        value: totalServers,
        icon: EasyMcpIcon,
        description: `${runningServers} running, ${stoppedServers} stopped, ${errorServers} errors`,
      },
      {
        title: "Total Calls",
        value: formatNumber(totalCalls),
        icon: Activity,
        description: "Tools, prompts, and resources",
      },
      {
        title: "Total Capabilities",
        value: formatNumber(totalCapabilities),
        icon: Zap,
        description: "Available tools, prompts, and resources",
      },
      {
        title: "System Uptime",
        value: uptimeDays > 0 ? `${uptimeDays}d` : `${uptimeHours}h`,
        icon: Clock,
        description:
          uptimeDays > 0
            ? `${uptimeDays} day${uptimeDays > 1 ? "s" : ""} uptime`
            : `${uptimeHours} hour${uptimeHours > 1 ? "s" : ""} uptime`,
      },
    ];
  }, [servers, mcpStats, status?.uptime]);

  return (
    <div
      className={cn(
        "grid grid-cols-1 gap-4 md:grid-cols-2 lg:grid-cols-4",
        className
      )}
    >
      {stats.map((stat, index) => (
        <MetricCard
          key={`${stat.title}-${index}`}
          title={stat.title}
          value={stat.value}
          icon={stat.icon}
          description={stat.description}
        />
      ))}
    </div>
  );
});
