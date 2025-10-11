"use client";

import * as React from "react";
import { cn } from "@/lib/utils";

interface AlertDialogProps {
  open: boolean;
  onOpenChange: (open: boolean) => void;
  children: React.ReactNode;
}

const AlertDialog: React.FC<AlertDialogProps> = ({
  open,
  onOpenChange,
  children,
}) => {
  const [isMounted, setIsMounted] = React.useState(open);

  React.useEffect(() => {
    if (open) {
      setIsMounted(true);
    } else {
      const timer = setTimeout(() => setIsMounted(false), 300);
      return () => clearTimeout(timer);
    }
  }, [open]);

  if (!isMounted) {
    return null;
  }

  return (
    <div
      className={cn("fixed inset-0 z-50", {
        "pointer-events-none": !open,
      })}
    >
      <div
        className={cn(
          "fixed inset-0 bg-black/50 transition-opacity duration-300",
          {
            "opacity-100": open,
            "opacity-0": !open,
          }
        )}
        onClick={() => onOpenChange(false)}
      />
      <div
        className={cn(
          "bg-background fixed top-[50%] left-[50%] z-50 grid w-full max-w-lg translate-x-[-50%] translate-y-[-50%] gap-4 border p-6 shadow-lg transition-all duration-300",
          {
            "scale-100 opacity-100": open,
            "scale-95 opacity-0": !open,
          }
        )}
      >
        {children}
      </div>
    </div>
  );
};

interface AlertDialogContentProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const AlertDialogContent: React.FC<AlertDialogContentProps> = ({
  className,
  children,
  ...props
}) => (
  <div className={cn("relative", className)} {...props}>
    {children}
  </div>
);

interface AlertDialogHeaderProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const AlertDialogHeader: React.FC<AlertDialogHeaderProps> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn(
      "flex flex-col space-y-1.5 text-center sm:text-left",
      className
    )}
    {...props}
  >
    {children}
  </div>
);

interface AlertDialogTitleProps
  extends React.HTMLAttributes<HTMLHeadingElement> {
  children: React.ReactNode;
}

const AlertDialogTitle: React.FC<AlertDialogTitleProps> = ({
  className,
  children,
  ...props
}) => (
  <h2
    className={cn(
      "text-lg leading-none font-semibold tracking-tight",
      className
    )}
    {...props}
  >
    {children}
  </h2>
);

interface AlertDialogDescriptionProps
  extends React.HTMLAttributes<HTMLParagraphElement> {
  children: React.ReactNode;
}

const AlertDialogDescription: React.FC<AlertDialogDescriptionProps> = ({
  className,
  children,
  ...props
}) => (
  <p className={cn("text-muted-foreground text-sm", className)} {...props}>
    {children}
  </p>
);

interface AlertDialogFooterProps extends React.HTMLAttributes<HTMLDivElement> {
  children: React.ReactNode;
}

const AlertDialogFooter: React.FC<AlertDialogFooterProps> = ({
  className,
  children,
  ...props
}) => (
  <div
    className={cn(
      "flex flex-col-reverse sm:flex-row sm:justify-end sm:space-x-2",
      className
    )}
    {...props}
  >
    {children}
  </div>
);

interface AlertDialogActionProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const AlertDialogAction: React.FC<AlertDialogActionProps> = ({
  className,
  children,
  ...props
}) => (
  <button
    className={cn(
      "bg-primary text-primary-foreground hover:bg-primary/90 focus-visible:ring-ring inline-flex h-9 items-center justify-center rounded-md px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-1 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
      className
    )}
    {...props}
  >
    {children}
  </button>
);

interface AlertDialogCancelProps
  extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  children: React.ReactNode;
}

const AlertDialogCancel: React.FC<AlertDialogCancelProps> = ({
  className,
  children,
  ...props
}) => (
  <button
    className={cn(
      "bg-background hover:bg-accent hover:text-accent-foreground border-input focus-visible:ring-ring inline-flex h-9 items-center justify-center rounded-md border px-4 py-2 text-sm font-medium whitespace-nowrap transition-colors focus-visible:ring-1 focus-visible:outline-none disabled:pointer-events-none disabled:opacity-50",
      className
    )}
    {...props}
  >
    {children}
  </button>
);

export {
  AlertDialog,
  AlertDialogContent,
  AlertDialogHeader,
  AlertDialogFooter,
  AlertDialogTitle,
  AlertDialogDescription,
  AlertDialogAction,
  AlertDialogCancel,
};
