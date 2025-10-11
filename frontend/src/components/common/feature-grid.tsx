"use client";

import { cn } from "@/lib/utils";
import { LucideIcon } from "lucide-react";
import { memo } from "react";

interface FeatureItemProps {
  icon: LucideIcon;
  title: string;
  description: string;
  className?: string;
}

export const FeatureItem = memo(function FeatureItem({
  icon: Icon,
  title,
  description,
  className,
}: FeatureItemProps) {
  return (
    <div
      className={cn(
        "flex items-start space-x-3 rounded-lg border p-4",
        className
      )}
    >
      <div className="bg-primary/10 rounded-lg p-2">
        <Icon className="text-primary h-4 w-4" />
      </div>
      <div>
        <h3 className="font-semibold">{title}</h3>
        <p className="text-muted-foreground text-sm">{description}</p>
      </div>
    </div>
  );
});

interface FeatureGridProps {
  features: Array<{
    icon: LucideIcon;
    title: string;
    description: string;
  }>;
  columns?: 1 | 2 | 3 | 4;
  className?: string;
}

export const FeatureGrid = memo(function FeatureGrid({
  features,
  columns = 2,
  className,
}: FeatureGridProps) {
  const gridCols = {
    1: "grid-cols-1",
    2: "grid-cols-1 md:grid-cols-2",
    3: "grid-cols-1 md:grid-cols-2 lg:grid-cols-3",
    4: "grid-cols-1 md:grid-cols-2 lg:grid-cols-4",
  };

  return (
    <div className={cn("grid gap-4", gridCols[columns], className)}>
      {features.map((feature, index) => (
        <FeatureItem
          key={index}
          icon={feature.icon}
          title={feature.title}
          description={feature.description}
        />
      ))}
    </div>
  );
});
