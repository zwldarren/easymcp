"use client";

import { cn } from "@/lib/utils";
import { memo } from "react";

interface StepItemProps {
  number: number;
  title: string;
  description: string;
  className?: string;
}

export const StepItem = memo(function StepItem({
  number,
  title,
  description,
  className,
}: StepItemProps) {
  return (
    <div
      className={cn(
        "flex items-start space-x-4 rounded-lg border p-4",
        className
      )}
    >
      <div className="bg-primary text-primary-foreground flex h-6 w-6 flex-shrink-0 items-center justify-center rounded-full text-sm font-medium">
        {number}
      </div>
      <div className="flex-1">
        <h4 className="font-medium">{title}</h4>
        <p className="text-muted-foreground text-sm">{description}</p>
      </div>
    </div>
  );
});

interface StepListProps {
  steps: Array<{
    title: string;
    description: string;
  }>;
  className?: string;
}

export const StepList = memo(function StepList({
  steps,
  className,
}: StepListProps) {
  return (
    <div className={cn("space-y-4", className)}>
      {steps.map((step, index) => (
        <StepItem
          key={index}
          number={index + 1}
          title={step.title}
          description={step.description}
        />
      ))}
    </div>
  );
});
