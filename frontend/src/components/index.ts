// Common components index - Centralized exports for better maintainability

// Layout Components
export { MainLayout } from "./layout/main-layout";
export { Sidebar } from "./layout/sidebar";

// State Components (Loading, Error, Empty)
export {
  ErrorState,
  LoadingState,
  EmptyState,
} from "./common/state-components";

// Generic Components
export { GenericDialog, type DialogAction } from "./common/generic-dialog";
export { MetricCard, type MetricCardProps } from "./common/metric-card";
export { LoadingSpinner, LoadingCard } from "./common/loading-spinner";
export { HealthStatusIcon } from "./common/health-status-icon";
export { McpIcon } from "./common/mcp-icon";

// Server Components
export { ServerCard } from "./common/server-card";
export {
  ServerStatusBadge,
  ServerCapabilities,
  ServerErrorAlert,
  ServerActionButtons,
} from "./common/server-card-parts";

// API Key Components
export {
  ApiKeyCard,
  ApiKeyGenerationDialog,
  ApiKeyDeletionDialog,
} from "./api-keys";

// Authentication Components
export { LoginForm } from "./auth/login-form";
export { RequireAuth } from "./auth/require-auth";

// Form Components
export { StatsGrid } from "./common/stats-grid";

// Error Handling
export { ErrorBoundary } from "./common/error-boundary";
export { Fallback } from "./common/fallback";

// New Common Components
export { FeatureGrid, FeatureItem } from "./common/feature-grid";
export { StepList, StepItem } from "./common/step-list";
export { CopyButton } from "./common/copy-button";

// Confirmation Dialog
export { ConfirmationDialog } from "./common/confirmation-dialog";

// Documentation Components
export { ServerSelector } from "./docs/server-selector";
export { CodeExample } from "./docs/code-example";
export { ParameterList, BenefitList } from "./docs/info-lists";
