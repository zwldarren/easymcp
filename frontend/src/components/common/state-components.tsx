"use client";

import { AlertCircle, RefreshCw } from "lucide-react";
import { Button } from "@/components/ui/button";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LoadingSpinner } from "./loading-spinner";

interface ErrorStateProps {
  title?: string;
  message?: string;
  onRetry?: () => void;
  className?: string;
}

export function ErrorState({
  title = "Something went wrong",
  message = "An unexpected error occurred. Please try again.",
  onRetry,
  className,
}: ErrorStateProps) {
  return (
    <Card className={`mx-auto max-w-md ${className || ""}`}>
      <CardHeader>
        <CardTitle className="text-destructive flex items-center">
          <AlertCircle className="mr-2 h-5 w-5" />
          {title}
        </CardTitle>
      </CardHeader>
      <CardContent>
        <div className="space-y-4">
          <p className="text-muted-foreground text-sm">{message}</p>
          {onRetry && (
            <Button onClick={onRetry} variant="outline" size="sm">
              <RefreshCw className="mr-2 h-4 w-4" />
              Try again
            </Button>
          )}
        </div>
      </CardContent>
    </Card>
  );
}

interface LoadingStateProps {
  title?: string;
  description?: string;
  className?: string;
}

export function LoadingState({
  title = "Loading",
  description = "Please wait...",
  className,
}: LoadingStateProps) {
  return (
    <div className={`flex items-center justify-center p-8 ${className || ""}`}>
      <div className="text-center">
        <LoadingSpinner size="lg" />
        <h3 className="mt-4 text-lg font-semibold">{title}</h3>
        <p className="text-muted-foreground">{description}</p>
      </div>
    </div>
  );
}

interface EmptyStateProps {
  icon?: React.ComponentType<{ className?: string }>;
  title: string;
  description?: string;
  action?: {
    label: string;
    onClick: () => void;
    variant?: "default" | "outline" | "secondary";
  };
  className?: string;
}

export function EmptyState({
  icon: Icon,
  title,
  description,
  action,
  className,
}: EmptyStateProps) {
  return (
    <div className={`py-12 text-center ${className || ""}`}>
      {Icon && (
        <div className="bg-muted mx-auto mb-4 flex h-12 w-12 items-center justify-center rounded-lg">
          <Icon className="text-muted-foreground h-6 w-6" />
        </div>
      )}
      <div className="space-y-2">
        <h3 className="text-lg font-semibold">{title}</h3>
        {description && (
          <p className="text-muted-foreground mx-auto max-w-sm">
            {description}
          </p>
        )}
        {action && (
          <Button
            onClick={action.onClick}
            variant={action.variant || "outline"}
            className="mt-4"
          >
            {action.label}
          </Button>
        )}
      </div>
    </div>
  );
}
