export const POLLING_INTERVALS = {
  SYSTEM_STATUS: 120000,
  SYSTEM_HEALTH: 120000,
  SYSTEM_METRICS: 120000,
  MCP_STATISTICS: 30000,
} as const;

export const STALE_TIME = {
  DEFAULT: 1000 * 60, // 1 minute
  SYSTEM_DATA: 1000 * 30, // 30 seconds
  REAL_TIME: 1000 * 10, // 10 seconds
} as const;
