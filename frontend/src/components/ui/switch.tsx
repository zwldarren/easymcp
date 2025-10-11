"use client";

import * as React from "react";

import { cn } from "@/lib/utils";

interface SwitchProps
  extends Omit<React.InputHTMLAttributes<HTMLInputElement>, "type"> {
  className?: string;
  onCheckedChange?: (checked: boolean) => void;
}

const Switch = React.forwardRef<HTMLInputElement, SwitchProps>(
  ({ className, onCheckedChange, checked, onChange, ...props }, ref) => (
    <label className="relative inline-flex cursor-pointer items-center">
      <input
        type="checkbox"
        className="peer sr-only"
        ref={ref}
        checked={checked}
        onChange={(e) => {
          if (onChange) onChange(e);
          if (onCheckedChange) onCheckedChange(e.target.checked);
        }}
        {...props}
      />
      <div
        className={cn(
          "peer bg-input peer-checked:bg-primary peer-focus:ring-ring/50 after:border-border h-6 w-11 rounded-full peer-focus:ring-4 peer-focus:outline-none after:absolute after:start-[2px] after:top-[2px] after:h-5 after:w-5 after:rounded-full after:border after:bg-white after:transition-all after:content-[''] peer-checked:after:translate-x-full peer-checked:after:border-white rtl:peer-checked:after:-translate-x-full",
          className
        )}
      />
    </label>
  )
);
Switch.displayName = "Switch";

export { Switch };
