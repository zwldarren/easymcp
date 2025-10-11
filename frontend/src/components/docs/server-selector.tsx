import React from "react";
import { Badge } from "@/components/ui/badge";
import { Select } from "@/components/ui/select";
import { useServers } from "@/hooks/use-api-queries";

interface ServerSelectorProps {
  selectedServer: string;
  onServerChange: (server: string) => void;
  id?: string;
  className?: string;
}

export function ServerSelector({
  selectedServer,
  onServerChange,
  id,
  className = "w-64",
}: ServerSelectorProps) {
  const { data: servers = [], isLoading } = useServers();

  return (
    <div className="bg-muted/30 rounded-lg border p-4">
      <div className="flex items-center space-x-4">
        <label htmlFor={id} className="text-sm font-medium">
          Select Server:
        </label>
        <Select
          id={id}
          value={selectedServer}
          onChange={(e) => onServerChange(e.target.value)}
          disabled={isLoading || servers.length === 0}
          className={className}
        >
          {isLoading ? (
            <option value="">Loading servers...</option>
          ) : servers.length === 0 ? (
            <option value="">No servers available</option>
          ) : (
            servers.map((server) => (
              <option key={server.name} value={server.name}>
                {server.name}
              </option>
            ))
          )}
        </Select>
        {selectedServer && (
          <Badge variant="outline" className="text-xs">
            Selected: {selectedServer}
          </Badge>
        )}
      </div>
    </div>
  );
}
