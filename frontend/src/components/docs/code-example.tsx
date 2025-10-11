import React from "react";
import { CopyButton } from "@/components/common/copy-button";

interface CodeExampleProps {
  title: string;
  code: string;
  children?: React.ReactNode;
}

export function CodeExample({ title, code, children }: CodeExampleProps) {
  return (
    <div className="space-y-2">
      <div className="flex items-center justify-between">
        <h4 className="font-medium">{title}</h4>
        <CopyButton text={code} />
      </div>
      <div className="overflow-x-auto rounded-lg bg-slate-900 p-4 text-slate-100">
        <pre className="text-sm">
          <code>{code}</code>
        </pre>
      </div>
      {children}
    </div>
  );
}
