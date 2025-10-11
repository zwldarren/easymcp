"use client";

import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { Badge } from "@/components/ui/badge";
import { Button } from "@/components/ui/button";
import { Key, Calendar, Clock, Eye, EyeOff, Trash2, Hash } from "lucide-react";
import { CopyButton } from "@/components/common/copy-button";
import { useState } from "react";
import { formatDateTime } from "@/lib/formatters";
import type { ApiKeyResponse } from "@/lib/api";
import { cn } from "@/lib/utils";

interface ApiKeyCardProps {
  apiKey: ApiKeyResponse;
  onDelete: (keyId: number) => void;
  onCopy: (keyId: number, fullKey?: string) => void;
}

export function ApiKeyCard({ apiKey, onDelete, onCopy }: ApiKeyCardProps) {
  const [showKey, setShowKey] = useState(false);

  const handleCopy = () => {
    const storedKey = localStorage.getItem(`api-key-${apiKey.id}`);
    if (storedKey) {
      onCopy(apiKey.id, storedKey);
    } else {
      onCopy(apiKey.id);
    }
  };

  const toggleKeyVisibility = () => {
    setShowKey(!showKey);
  };

  const getScopesBadge = (scopes: string[]) => {
    if (scopes.includes("admin")) {
      return <Badge variant="default">Admin</Badge>;
    }
    return <Badge variant="outline">{scopes.length} scopes</Badge>;
  };

  const truncateHash = (hash: string) => {
    return hash.length > 16 ? `${hash.slice(0, 8)}...${hash.slice(-8)}` : hash;
  };

  const getStoredKey = () => {
    const storedKey = localStorage.getItem(`api-key-${apiKey.id}`);
    if (!storedKey) return null;

    if (showKey) {
      return storedKey;
    }
    return `${storedKey.substring(0, 8)}...${storedKey.substring(storedKey.length - 8)}`;
  };

  const hasStoredKey = !!localStorage.getItem(`api-key-${apiKey.id}`);

  return (
    <Card className={cn(!apiKey.is_active && "opacity-60")}>
      <CardHeader className="pb-3">
        <div className="flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <Key className="text-muted-foreground h-5 w-5" />
            <div className="flex flex-col">
              <CardTitle className="text-lg">{apiKey.name}</CardTitle>
              {apiKey.description && (
                <p className="text-muted-foreground mt-1 line-clamp-2 text-sm">
                  {apiKey.description}
                </p>
              )}
            </div>
          </div>
          <div className="flex items-center space-x-2">
            {getScopesBadge(apiKey.scopes)}
          </div>
        </div>
      </CardHeader>

      <CardContent className="space-y-4">
        {/* API Key Display */}
        {hasStoredKey && (
          <div className="space-y-2">
            <label className="text-muted-foreground text-sm font-medium">
              API Key
            </label>
            <div className="flex items-center space-x-2">
              <code className="bg-muted flex-1 rounded px-3 py-2 font-mono text-sm break-all">
                {getStoredKey()}
              </code>
              <div className="flex space-x-1">
                <Button
                  variant="outline"
                  size="sm"
                  onClick={toggleKeyVisibility}
                  title={showKey ? "Hide key" : "Show key"}
                >
                  {showKey ? (
                    <EyeOff className="h-4 w-4" />
                  ) : (
                    <Eye className="h-4 w-4" />
                  )}
                </Button>
                <CopyButton
                  text={localStorage.getItem(`api-key-${apiKey.id}`) || ""}
                  size="sm"
                  variant="outline"
                  onSuccess={() => handleCopy()}
                  showToast={false}
                />
              </div>
            </div>
          </div>
        )}

        {/* Key Information */}
        <div className="grid grid-cols-1 gap-4 text-sm md:grid-cols-2">
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Calendar className="text-muted-foreground h-4 w-4" />
              <span className="text-muted-foreground">Created:</span>
              <span>{formatDateTime(apiKey.created_at)}</span>
            </div>
            <div className="flex items-center space-x-2">
              <Clock className="text-muted-foreground h-4 w-4" />
              <span className="text-muted-foreground">Last Used:</span>
              <span>{formatDateTime(apiKey.last_used)}</span>
            </div>
          </div>
          <div className="space-y-2">
            <div className="flex items-center space-x-2">
              <Hash className="text-muted-foreground h-4 w-4" />
              <span className="text-muted-foreground">Hash:</span>
              <span className="font-mono text-xs">
                {truncateHash(apiKey.key_hash)}
              </span>
            </div>
          </div>
        </div>

        {/* Scopes */}
        <div className="space-y-2">
          <label className="text-muted-foreground text-sm font-medium">
            Permissions
          </label>
          <div className="flex flex-wrap gap-1">
            {apiKey.scopes.map((scope) => (
              <Badge key={scope} variant="secondary" className="text-xs">
                {scope}
              </Badge>
            ))}
          </div>
        </div>

        {/* Actions */}
        <div className="flex justify-end space-x-2 pt-2">
          <Button
            variant="destructive"
            size="sm"
            onClick={() => onDelete(apiKey.id)}
          >
            <Trash2 className="mr-2 h-4 w-4" />
            Delete
          </Button>
        </div>
      </CardContent>
    </Card>
  );
}
