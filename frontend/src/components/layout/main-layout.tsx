"use client";

import { cn } from "@/lib/utils";
import { Sidebar } from "./sidebar";

interface MainLayoutProps {
  children: React.ReactNode;
  className?: string;
}

export function MainLayout({ children, className }: MainLayoutProps) {
  return (
    <div className="bg-background min-h-screen">
      <div className="flex">
        <Sidebar />
        <div className="ml-64 flex flex-1 flex-col">
          <main className={cn("flex-1 p-6", className)}>{children}</main>
        </div>
      </div>
    </div>
  );
}
