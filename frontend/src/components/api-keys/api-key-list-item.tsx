"use client";

import { Button } from "@/components/ui/button";
import { Key, Trash2, Hash, Calendar } from "lucide-react";
import type { ApiKeyResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ApiKeyListItemProps {
  apiKey: ApiKeyResponse;
  onDelete: (keyId: number) => void;
}

export function ApiKeyListItem({ apiKey, onDelete }: ApiKeyListItemProps) {
  // Format creation date
  const formatDate = (dateString: string) => {
    return new Date(dateString).toLocaleDateString("en-US", {
      year: "numeric",
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit",
    });
  };

  // Truncate hash for display
  const truncateHash = (hash: string) => {
    return hash.length > 16 ? `${hash.slice(0, 8)}...${hash.slice(-8)}` : hash;
  };

  return (
    <div
      className={cn(
        "group border-border/40 bg-card hover:border-border/80 flex items-center justify-between rounded-lg border p-4 transition-all duration-200 hover:shadow-sm",
        !apiKey.is_active && "opacity-50"
      )}
    >
      <div className="flex items-center space-x-3">
        <div className="bg-primary/10 flex h-10 w-10 items-center justify-center rounded-full">
          <Key className="text-primary h-5 w-5" />
        </div>
        <div className="flex-1">
          <h3 className="text-foreground font-semibold">{apiKey.name}</h3>
          {apiKey.description && (
            <p className="text-muted-foreground mt-1 line-clamp-2 text-sm">
              {apiKey.description}
            </p>
          )}
          <div className="text-muted-foreground mt-2 flex items-center space-x-4 text-sm">
            <div className="flex items-center space-x-1">
              <Calendar className="h-3 w-3" />
              <span>Created: {formatDate(apiKey.created_at)}</span>
            </div>
            <div className="flex items-center space-x-1">
              <Hash className="h-3 w-3" />
              <span className="font-mono text-xs">
                {truncateHash(apiKey.key_hash)}
              </span>
            </div>
          </div>
        </div>
      </div>

      <Button
        variant="ghost"
        size="sm"
        onClick={() => onDelete(apiKey.id)}
        className="hover:bg-destructive/10 hover:text-destructive opacity-0 transition-opacity duration-200 group-hover:opacity-100"
        title="Delete API key"
      >
        <Trash2 className="h-4 w-4" />
      </Button>
    </div>
  );
}
