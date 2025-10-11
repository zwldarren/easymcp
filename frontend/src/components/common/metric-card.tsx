"use client";

import { cn } from "@/lib/utils";
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/card";
import { LucideIcon, TrendingUp, TrendingDown } from "@/lib/icons";
import { memo } from "react";

export interface MetricCardProps {
  title: string;
  value: string | number;
  icon: LucideIcon;
  description?: string;
  trend?: {
    value: number;
    type: "increase" | "decrease";
  };
  className?: string;
  onClick?: () => void;
}

export const MetricCard = memo(function MetricCard({
  title,
  value,
  icon: Icon,
  description,
  trend,
  className,
  onClick,
}: MetricCardProps) {
  return (
    <Card
      className={cn(
        "transition-all duration-200 hover:-translate-y-1 hover:shadow-lg",
        onClick && "cursor-pointer",
        className
      )}
      onClick={onClick}
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
          {trend && (
            <div
              className={cn(
                "flex items-center space-x-1 text-xs font-medium",
                trend.type === "increase"
                  ? "text-green-600 dark:text-green-500"
                  : "text-red-600 dark:text-red-500"
              )}
            >
              {trend.type === "increase" ? (
                <TrendingUp className="h-3 w-3" />
              ) : (
                <TrendingDown className="h-3 w-3" />
              )}
              <span>{Math.abs(trend.value)}%</span>
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

// Re-export for compatibility
export { MetricCard as MetricCardComponent };
