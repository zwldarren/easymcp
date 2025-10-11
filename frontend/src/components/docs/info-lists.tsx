import React from "react";

interface ParameterListProps {
  parameters: Array<{
    name: string;
    description: string;
  }>;
}

export function ParameterList({ parameters }: ParameterListProps) {
  return (
    <div className="rounded-lg border p-4">
      <h4 className="mb-2 font-medium">Parameters</h4>
      <ul className="text-muted-foreground space-y-1 text-sm">
        {parameters.map((param) => (
          <li key={param.name}>
            • <code className="bg-muted rounded px-1">{param.name}</code>:
            {param.description}
          </li>
        ))}
      </ul>
    </div>
  );
}

interface BenefitListProps {
  benefits: string[];
}

export function BenefitList({ benefits }: BenefitListProps) {
  return (
    <div className="rounded-lg border p-4">
      <h4 className="mb-2 font-medium">Benefits</h4>
      <ul className="text-muted-foreground space-y-1 text-sm">
        {benefits.map((benefit) => (
          <li key={benefit}>• {benefit}</li>
        ))}
      </ul>
    </div>
  );
}
