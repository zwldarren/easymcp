// Design System Configuration
export const designSystem = {
  // Breakpoints
  breakpoints: {
    sm: "640px",
    md: "768px",
    lg: "1024px",
    xl: "1280px",
    "2xl": "1536px",
  },

  // Spacing Scale
  spacing: {
    xs: "0.25rem", // 4px
    sm: "0.5rem", // 8px
    md: "1rem", // 16px
    lg: "1.5rem", // 24px
    xl: "2rem", // 32px
    "2xl": "3rem", // 48px
    "3xl": "4rem", // 64px
  },

  // Border Radius
  radius: {
    xs: "calc(var(--radius) - 6px)",
    sm: "calc(var(--radius) - 4px)",
    md: "calc(var(--radius) - 2px)",
    lg: "var(--radius)",
    xl: "calc(var(--radius) + 4px)",
    "2xl": "calc(var(--radius) + 8px)",
    full: "9999px",
  },

  // Shadows
  shadows: {
    sm: "0 1px 2px 0 rgb(0 0 0 / 0.05)",
    md: "0 4px 6px -1px rgb(0 0 0 / 0.1), 0 2px 4px -2px rgb(0 0 0 / 0.1)",
    lg: "0 10px 15px -3px rgb(0 0 0 / 0.1), 0 4px 6px -4px rgb(0 0 0 / 0.1)",
    xl: "0 20px 25px -5px rgb(0 0 0 / 0.1), 0 8px 10px -6px rgb(0 0 0 / 0.1)",
    "2xl": "0 25px 50px -12px rgb(0 0 0 / 0.25)",
  },

  // Transitions
  transitions: {
    fast: "all 0.15s cubic-bezier(0.4, 0, 0.2, 1)",
    normal: "all 0.2s cubic-bezier(0.4, 0, 0.2, 1)",
    slow: "all 0.3s cubic-bezier(0.4, 0, 0.2, 1)",
  },

  // Z-index Scale
  zIndex: {
    dropdown: 1000,
    sticky: 1020,
    fixed: 1030,
    modal: 1040,
    popover: 1050,
    tooltip: 1060,
  },
} as const;

// Status Colors Mapping
export const statusColors = {
  success: {
    text: "text-green-600 dark:text-green-500",
    bg: "bg-green-500",
    border: "border-green-200 dark:border-green-800",
    background: "bg-green-50 dark:bg-green-950",
  },
  warning: {
    text: "text-yellow-600 dark:text-yellow-500",
    bg: "bg-yellow-500",
    border: "border-yellow-200 dark:border-yellow-800",
    background: "bg-yellow-50 dark:bg-yellow-950",
  },
  error: {
    text: "text-red-600 dark:text-red-500",
    bg: "bg-red-500",
    border: "border-red-200 dark:border-red-800",
    background: "bg-red-50 dark:bg-red-950",
  },
  info: {
    text: "text-blue-600 dark:text-blue-500",
    bg: "bg-blue-500",
    border: "border-blue-200 dark:border-blue-800",
    background: "bg-blue-50 dark:bg-blue-950",
  },
  stopped: {
    text: "text-gray-600 dark:text-gray-400",
    bg: "bg-gray-400",
    border: "border-gray-200 dark:border-gray-700",
    background: "bg-gray-50 dark:bg-gray-900",
  },
  running: {
    text: "text-green-600 dark:text-green-500",
    bg: "bg-green-500",
    border: "border-green-200 dark:border-green-800",
    background: "bg-green-50 dark:bg-green-950",
  },
  starting: {
    text: "text-yellow-600 dark:text-yellow-500",
    bg: "bg-yellow-500",
    border: "border-yellow-200 dark:border-yellow-800",
    background: "bg-yellow-50 dark:bg-yellow-950",
  },
  stopping: {
    text: "text-orange-600 dark:text-orange-500",
    bg: "bg-orange-500",
    border: "border-orange-200 dark:border-orange-800",
    background: "bg-orange-50 dark:bg-orange-950",
  },
} as const;

// Server Type Icons and Colors
export const serverTypeConfig = {
  stdio: {
    icon: "Database",
    color: "blue",
    description: "Local process via standard I/O",
  },
  sse: {
    icon: "Activity",
    color: "green",
    description: "Server-Sent Events for real-time communication",
  },
  "streamable-http": {
    icon: "Plug",
    color: "purple",
    description: "HTTP-based communication with streaming support",
  },
} as const;

// Animation Presets
export const animations = {
  fadeIn: {
    initial: { opacity: 0 },
    animate: { opacity: 1 },
    exit: { opacity: 0 },
    transition: { duration: 0.2 },
  },
  slideUp: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
    exit: { opacity: 0, y: 20 },
    transition: { duration: 0.3, ease: "easeOut" },
  },
  scaleIn: {
    initial: { opacity: 0, scale: 0.95 },
    animate: { opacity: 1, scale: 1 },
    exit: { opacity: 0, scale: 0.95 },
    transition: { duration: 0.2 },
  },
  staggerContainer: {
    initial: { opacity: 0 },
    animate: {
      opacity: 1,
      transition: {
        staggerChildren: 0.1,
        delayChildren: 0.2,
      },
    },
  },
  staggerItem: {
    initial: { opacity: 0, y: 20 },
    animate: { opacity: 1, y: 0 },
  },
} as const;

// Common Layout Patterns
export const layouts = {
  pageContainer: "container-custom py-6 space-y-6",
  section: "space-y-4",
  cardGrid:
    "grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4",
  responsiveFlex:
    "flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between",
  headerActions: "flex flex-col gap-3 sm:flex-row sm:items-center",
} as const;

// Loading States
export const loadingStates = {
  skeleton: "animate-pulse rounded-md bg-muted",
  spinner:
    "animate-spin rounded-full border-2 border-current border-t-transparent",
  pulse: "animate-pulse",
  bounce: "animate-bounce",
} as const;
