/**
 * Status and styling utilities
 */

import { type VariantProps } from "class-variance-authority";
import { badgeVariants } from "@/components/ui/badge";
import { statusColors, serverTypeConfig } from "./design-system";

type BadgeVariant = VariantProps<typeof badgeVariants>["variant"];

/**
 * Get status color classes
 */
export function getStatusColor(status: string): string {
  const statusKey = status.toLowerCase() as keyof typeof statusColors;
  return statusColors[statusKey]?.text || statusColors.stopped.text;
}

/**
 * Get status background color classes
 */
export function getStatusBgColor(status: string): string {
  const statusKey = status.toLowerCase() as keyof typeof statusColors;
  return statusColors[statusKey]?.bg || statusColors.stopped.bg;
}

export function getServerStatusBadgeVariant(status: string): BadgeVariant {
  switch (status.toLowerCase()) {
    case "running":
      return "default";
    case "error":
      return "destructive";
    case "starting":
    case "stopping":
      return "outline";
    default:
      return "secondary";
  }
}

export function getHealthBadgeVariant(status: string): BadgeVariant {
  switch (status.toLowerCase()) {
    case "healthy":
      return "default";
    case "degraded":
      return "secondary";
    case "unhealthy":
      return "destructive";
    default:
      return "outline";
  }
}

/**
 * Get server type configuration
 */
export function getServerTypeConfig(type: string) {
  const typeKey = type as keyof typeof serverTypeConfig;
  return (
    serverTypeConfig[typeKey] || {
      icon: "Server",
      color: "gray",
      description: "Unknown server type",
    }
  );
}
