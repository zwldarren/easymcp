export interface ApiError {
  code?: string;
  detail?: string;
  message?: string;
  field?: string;
  timestamp?: string;
}

export interface ValidationError extends ApiError {
  field: string;
  validation_errors?: Record<string, string[]>;
}

export interface NetworkError extends ApiError {
  code: "NETWORK_ERROR";
  message: string;
}

export interface AuthenticationError extends ApiError {
  code: "AUTHENTICATION_ERROR";
  message: string;
}

export interface AuthorizationError extends ApiError {
  code: "AUTHORIZATION_ERROR";
  message: string;
}

export interface NotFoundError extends ApiError {
  code: "NOT_FOUND";
  message: string;
}

export interface ServerError extends ApiError {
  code: "SERVER_ERROR";
  message: string;
}

export type KnownError =
  | ValidationError
  | NetworkError
  | AuthenticationError
  | AuthorizationError
  | NotFoundError
  | ServerError;

export function isApiError(error: unknown): error is ApiError {
  return (
    typeof error === "object" &&
    error !== null &&
    ("code" in error || "message" in error || "detail" in error)
  );
}

export function isValidationError(error: unknown): error is ValidationError {
  return isApiError(error) && "field" in error;
}

export function isNetworkError(error: unknown): error is NetworkError {
  return isApiError(error) && error.code === "NETWORK_ERROR";
}

export function getErrorMessage(error: unknown): string {
  if (isValidationError(error)) {
    return (
      error.detail ||
      error.message ||
      `Validation error for field: ${error.field}`
    );
  }

  if (isNetworkError(error)) {
    return "Network connection failed. Please check your internet connection.";
  }

  if (isApiError(error)) {
    return error.detail || error.message || "An unexpected error occurred";
  }

  if (error instanceof Error) {
    return error.message;
  }

  return "An unexpected error occurred";
}

export function getErrorCode(error: unknown): string | undefined {
  if (isApiError(error)) {
    return error.code;
  }
  return undefined;
}
