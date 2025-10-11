"use client";

import React from "react";
import { CheckCircle, XCircle, AlertTriangle, RefreshCw } from "@/lib/icons";
import { memo } from "react";

interface HealthStatusIconProps {
  status: string;
}

export const HealthStatusIcon = memo(function HealthStatusIcon({
  status,
}: HealthStatusIconProps): React.JSX.Element {
  switch (status) {
    case "healthy":
      return <CheckCircle className="h-5 w-5 text-green-500" />;
    case "degraded":
      return <AlertTriangle className="h-5 w-5 text-yellow-500" />;
    case "unhealthy":
      return <XCircle className="h-5 w-5 text-red-500" />;
    default:
      return <RefreshCw className="h-5 w-5 text-gray-500" />;
  }
});
