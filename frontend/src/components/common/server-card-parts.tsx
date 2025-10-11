"use client";

import { cn } from "@/lib/utils";
import { getStatusColor, getStatusBgColor } from "@/lib/status";
import { memo } from "react";

interface ServerStatusBadgeProps {
  state: string;
}

export const ServerStatusBadge = memo(function ServerStatusBadge({
  state,
}: ServerStatusBadgeProps) {
  return (
    <div className="flex items-center space-x-1">
      <div
        className={cn(
          "h-2 w-2 rounded-full",
          getStatusBgColor(state || "stopped")
        )}
      ></div>
      <span
        className={cn("text-xs capitalize", getStatusColor(state || "stopped"))}
      >
        {state || "stopped"}
      </span>
    </div>
  );
});

interface ServerCapabilitiesProps {
  capabilities?: Record<string, number>;
}

export const ServerCapabilities = memo(function ServerCapabilities({
  capabilities,
}: ServerCapabilitiesProps) {
  return (
    <div className="mb-4 grid grid-cols-3 gap-2">
      <div className="bg-muted/50 rounded-lg p-2 text-center">
        <div className="mb-1 flex items-center justify-center">
          <Wrench className="text-primary h-4 w-4" />
        </div>
        <div className="text-primary text-lg font-semibold">
          {capabilities?.tools || 0}
        </div>
        <div className="text-muted-foreground text-xs">Tools</div>
      </div>
      <div className="bg-muted/50 rounded-lg p-2 text-center">
        <div className="mb-1 flex items-center justify-center">
          <MessageSquare className="text-primary h-4 w-4" />
        </div>
        <div className="text-primary text-lg font-semibold">
          {capabilities?.prompts || 0}
        </div>
        <div className="text-muted-foreground text-xs">Prompts</div>
      </div>
      <div className="bg-muted/50 rounded-lg p-2 text-center">
        <div className="mb-1 flex items-center justify-center">
          <Folder className="text-primary h-4 w-4" />
        </div>
        <div className="text-primary text-lg font-semibold">
          {capabilities?.resources || 0}
        </div>
        <div className="text-muted-foreground text-xs">Resources</div>
      </div>
    </div>
  );
});

interface ServerErrorAlertProps {
  error?: string;
}

export const ServerErrorAlert = memo(function ServerErrorAlert({
  error,
}: ServerErrorAlertProps) {
  if (!error) return null;

  return (
    <div className="mb-3 rounded-md border border-red-200 bg-red-50 p-3 text-sm dark:border-red-900 dark:bg-red-950/50">
      <div className="flex items-start gap-2">
        <AlertTriangle className="mt-0.5 h-4 w-4 text-red-600 dark:text-red-500" />
        <span className="text-red-700 dark:text-red-300">{error}</span>
      </div>
    </div>
  );
});

interface ServerActionButtonsProps {
  serverName: string;
  isRunning: boolean;
  isStarting: boolean;
  isStopping: boolean;
  onStart: (name: string) => void;
  onStop: (name: string) => void;
}

export const ServerActionButtons = memo(function ServerActionButtons({
  serverName,
  isRunning,
  isStarting,
  isStopping,
  onStart,
  onStop,
}: ServerActionButtonsProps) {
  return (
    <div className="flex">
      <Button
        variant={isRunning ? "outline" : "default"}
        size="sm"
        className="flex-1"
        onClick={() => (isRunning ? onStop(serverName) : onStart(serverName))}
        disabled={isStarting || isStopping}
      >
        {isStarting ? (
          <>
            <LoadingSpinner size="sm" />
            Starting...
          </>
        ) : isStopping ? (
          <>
            <LoadingSpinner size="sm" />
            Stopping...
          </>
        ) : isRunning ? (
          <>
            <Pause className="mr-2 h-4 w-4" />
            Stop
          </>
        ) : (
          <>
            <Play className="mr-2 h-4 w-4" />
            Start
          </>
        )}
      </Button>
    </div>
  );
});

// Import required components
import { Button } from "@/components/ui/button";
import { LoadingSpinner } from "./loading-spinner";
import {
  Wrench,
  MessageSquare,
  Folder,
  Play,
  Pause,
  AlertTriangle,
} from "lucide-react";
