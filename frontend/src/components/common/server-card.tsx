"use client";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "./loading-spinner";
import { CopyButton } from "./copy-button";
import { Activity, Plug, Settings, Trash2 } from "lucide-react";
import { McpIcon } from "./mcp-icon";
import type { ServerWithStatus } from "@/types";
import { memo, useCallback } from "react";
import {
  ServerStatusBadge,
  ServerCapabilities,
  ServerErrorAlert,
  ServerActionButtons,
} from "./server-card-parts";

interface ServerCardProps {
  server: ServerWithStatus;
  onStart?: (serverName: string) => void;
  onStop?: (serverName: string) => void;
  onEdit?: (server: ServerWithStatus) => void;
  onDelete?: (serverName: string) => void;
  className?: string;
  isDeleting?: boolean;
}

const typeIcons: Record<
  string,
  React.ComponentType<React.SVGProps<SVGSVGElement>>
> = {
  stdio: McpIcon,
  sse: Activity,
  "streamable-http": Plug,
};

export const ServerCard = memo(function ServerCard({
  server,
  onStart,
  onStop,
  onEdit,
  onDelete,
  className,
  isDeleting,
}: ServerCardProps) {
  const TypeIcon = typeIcons[server.config.transport.type];

  // Generate server URL (match backend prefix /api)
  const baseUrl = process.env.NEXT_PUBLIC_API_URL || "http://localhost:8000";
  const serverUrl = `${baseUrl.replace(/\/$/, "")}/servers/${server.name}/mcp`;

  const handleStart = useCallback(
    () => onStart?.(server.name),
    [onStart, server.name]
  );
  const handleStop = useCallback(
    () => onStop?.(server.name),
    [onStop, server.name]
  );
  const handleEdit = useCallback(() => onEdit?.(server), [onEdit, server]);
  const handleDelete = useCallback(
    () => onDelete?.(server.name),
    [onDelete, server.name]
  );

  const isRunning = server.status?.state === "running";
  const isStarting = server.status?.state === "starting";
  const isStopping = server.status?.state === "stopping";

  return (
    <Card
      className={cn(
        "border-border/50 hover:border-primary/30 transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
        className
      )}
    >
      <CardHeader className="pb-3">
        <div className="flex items-start justify-between">
          <div className="flex items-center space-x-3">
            <div className="icon-container">
              <TypeIcon className="h-5 w-5" />
            </div>
            <div>
              <CardTitle className="text-base">{server.name}</CardTitle>
              <div className="mt-1 flex items-center space-x-2">
                <Badge variant="outline" className="text-xs">
                  {server.config.transport.type}
                </Badge>
                <ServerStatusBadge state={server.status?.state || "stopped"} />
              </div>
              <div className="mt-2 flex items-center space-x-2">
                <div className="min-w-0 flex-1">
                  <div className="text-muted-foreground bg-muted truncate rounded px-2 py-1 font-mono text-xs">
                    {serverUrl}
                  </div>
                </div>
                <CopyButton
                  text={serverUrl}
                  size="icon"
                  className="h-6 w-6 flex-shrink-0"
                />
              </div>
            </div>
          </div>
          <div className="flex space-x-1">
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleEdit}
            >
              <Settings className="h-4 w-4" />
            </Button>
            <Button
              variant="ghost"
              size="icon"
              className="h-8 w-8"
              onClick={handleDelete}
              disabled={isStarting || isStopping || isDeleting}
            >
              {isDeleting ? (
                <LoadingSpinner size="sm" />
              ) : (
                <Trash2 className="h-4 w-4" />
              )}
            </Button>
          </div>
        </div>
      </CardHeader>

      <CardContent className="pt-0">
        <ServerCapabilities capabilities={server.status?.capabilities} />
        <ServerErrorAlert error={server.status?.error} />

        <ServerActionButtons
          serverName={server.name}
          isRunning={!!isRunning}
          isStarting={!!isStarting}
          isStopping={!!isStopping}
          onStart={handleStart}
          onStop={handleStop}
        />
      </CardContent>
    </Card>
  );
});
