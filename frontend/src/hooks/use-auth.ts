"use client";

import React, {
  createContext,
  useContext,
  ReactNode,
  useReducer,
  useEffect,
} from "react";
import { useMutation, useQueryClient } from "@tanstack/react-query";
import { toast } from "react-hot-toast";
import {
  api,
  LoginRequest,
  ChangePasswordRequest,
  UserResponse,
} from "@/lib/api";

interface AuthState {
  user: UserResponse | null;
  isAuthenticated: boolean;
  isLoading: boolean;
}

interface AuthContextType extends AuthState {
  login: (credentials: LoginRequest) => Promise<void>;
  logout: () => Promise<void>;
  changePassword: (data: ChangePasswordRequest) => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

type AuthAction =
  | { type: "SET_USER"; payload: UserResponse | null }
  | { type: "SET_LOADING"; payload: boolean }
  | { type: "LOGOUT" };

const authReducer = (state: AuthState, action: AuthAction): AuthState => {
  switch (action.type) {
    case "SET_USER":
      return {
        ...state,
        user: action.payload,
        isAuthenticated: !!action.payload,
        isLoading: false,
      };
    case "SET_LOADING":
      return {
        ...state,
        isLoading: action.payload,
      };
    case "LOGOUT":
      return {
        user: null,
        isAuthenticated: false,
        isLoading: false,
      };
    default:
      return state;
  }
};

const initialState: AuthState = {
  user: null,
  isAuthenticated: false,
  isLoading: true,
};

const TOKEN_KEY = "easymcp_auth_token";

const getStoredToken = (): string | null => {
  if (typeof window !== "undefined") {
    const token = localStorage.getItem(TOKEN_KEY);
    return token;
  }
  return null;
};

const setStoredToken = (token: string): void => {
  if (typeof window !== "undefined") {
    localStorage.setItem(TOKEN_KEY, token);
  }
};

const removeStoredToken = (): void => {
  if (typeof window !== "undefined") {
    localStorage.removeItem(TOKEN_KEY);
  }
};

const setupAuthInterceptor = (token: string | null) => {
  api.setAuthToken(token);
};

export function AuthProvider({ children }: { children: ReactNode }) {
  const [state, dispatch] = useReducer(authReducer, initialState);
  const queryClient = useQueryClient();

  useEffect(() => {
    const token = getStoredToken();
    if (token) {
      setupAuthInterceptor(token);
      api
        .getCurrentUser()
        .then((user) => {
          dispatch({ type: "SET_USER", payload: user });
        })
        .catch(() => {
          removeStoredToken();
          setupAuthInterceptor(null);
          dispatch({ type: "LOGOUT" });
        });
    } else {
      setupAuthInterceptor(null);
      dispatch({ type: "SET_LOADING", payload: false });
    }
  }, []);

  const loginMutation = useMutation({
    mutationFn: (credentials: LoginRequest) => api.login(credentials),
    onSuccess: (data) => {
      setStoredToken(data.access_token);
      setupAuthInterceptor(data.access_token);
      dispatch({ type: "SET_USER", payload: data.user });
      toast.success(`Welcome back, ${data.user.username}!`);
    },
    onError: (error: Error) => {
      console.error("Login failed:", error);
      toast.error(error.message || "Login failed");
    },
  });

  const logoutMutation = useMutation({
    mutationFn: () => api.logout(),
    onSuccess: () => {
      removeStoredToken();
      setupAuthInterceptor(null);
      dispatch({ type: "LOGOUT" });
      queryClient.clear();
      toast.success("Logged out successfully");
    },
    onError: (error: Error) => {
      removeStoredToken();
      setupAuthInterceptor(null);
      dispatch({ type: "LOGOUT" });
      queryClient.clear();
      toast.error(error.message || "Logout failed");
    },
  });

  const changePasswordMutation = useMutation({
    mutationFn: (data: ChangePasswordRequest) => api.changePassword(data),
    onSuccess: () => {
      toast.success("Password changed successfully");
    },
    onError: (error: Error) => {
      toast.error(error.message || "Failed to change password");
    },
  });

  const login = async (credentials: LoginRequest) => {
    await loginMutation.mutateAsync(credentials);
  };

  const logout = async () => {
    await logoutMutation.mutateAsync();
  };

  const changePassword = async (data: ChangePasswordRequest) => {
    await changePasswordMutation.mutateAsync(data);
  };

  const value: AuthContextType = {
    ...state,
    login,
    logout,
    changePassword,
  };

  return React.createElement(AuthContext.Provider, { value }, children);
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
