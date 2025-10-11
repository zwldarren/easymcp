"use client";

import { cn } from "@/lib/utils";

interface EasyMcpIconProps {
  className?: string;
}

export function EasyMcpIcon({ className }: EasyMcpIconProps) {
  return (
    <svg
      xmlns="http://www.w3.org/2000/svg"
      viewBox="0 0 24 24"
      fill="currentColor"
      className={cn("h-6 w-6", className)}
    >
      <path
        d="M8.312 2.343a2.588 2.588 0 013.61 0l9.626 9.44a.863.863 0 001.203 0 .823.823 0 000-1.18l-9.626-9.44a4.313 4.313 0 00-6.016 0 4.116 4.116 0 00-1.204 3.54 4.3 4.3 0 00-3.609 1.18l-.05.05a4.115 4.115 0 000 5.9l8.706 8.537a.274.274 0 010 .393l-1.788 1.754a.823.823 0 000 1.18.863.863 0 001.203 0l1.788-1.753a1.92 1.92 0 000-2.754l-8.706-8.538a2.47 2.47 0 010-3.54l.05-.049a2.588 2.588 0 013.607-.003l7.172 7.034.002.002.098.097a.863.863 0 001.204 0 .823.823 0 000-1.18l-7.273-7.133a2.47 2.47 0 01.003-3.537z"
        opacity="0.9"
      />
    </svg>
  );
}
