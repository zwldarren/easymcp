import React from "react";
import { ServerCard } from "@/components/common/server-card";
import { ServerGridSkeleton } from "@/components/common/skeleton";
import type { ServerWithStatus } from "@/types";

interface ServerGridProps {
  servers: ServerWithStatus[];
  onStartServer: (name: string) => void;
  onStopServer: (name: string) => void;
  onConfigureServer: (server: ServerWithStatus) => void;
  onDeleteServer: (name: string) => void;
  isStarting?: boolean;
  isStopping?: boolean;
  isLoading?: boolean;
}

export const ServerGrid = React.memo(function ServerGrid({
  servers,
  onStartServer,
  onStopServer,
  onConfigureServer,
  onDeleteServer,
  isLoading = false,
}: ServerGridProps) {
  if (isLoading) {
    return <ServerGridSkeleton />;
  }

  if (servers.length === 0) {
    return (
      <div className="py-12 text-center" role="status" aria-live="polite">
        <div className="text-muted-foreground text-lg">No servers found</div>
        <div className="text-muted-foreground mt-2 text-sm">
          Try adjusting your filters or add a new server.
        </div>
      </div>
    );
  }

  return (
    <div
      className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-3"
      role="list"
      aria-label="Servers list"
    >
      {servers.map((server) => (
        <ServerCard
          key={server.name}
          server={server}
          onStart={() => onStartServer(server.name)}
          onStop={() => onStopServer(server.name)}
          onEdit={() => onConfigureServer(server)}
          onDelete={() => onDeleteServer(server.name)}
        />
      ))}
    </div>
  );
});
