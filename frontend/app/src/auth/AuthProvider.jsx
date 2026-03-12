import { createContext, useContext, useEffect } from "react";
import { useMutation, useQuery } from "@tanstack/react-query";

import { sessionApi } from "../lib/api";
import { queryClient } from "../lib/queryClient";

const AuthContext = createContext(null);

function applyUiPreferences(uiPreferences) {
  const root = document.documentElement;
  const themeMode = uiPreferences?.theme_mode || "system";
  const layoutMode = uiPreferences?.layout_mode || "standard";
  const accentColor = uiPreferences?.accent_color || "#0b57d0";
  root.dataset.themeMode = themeMode;
  root.dataset.layoutMode = layoutMode;
  root.style.setProperty("--accent-color", accentColor);
}

export function AuthProvider({ children }) {
  const sessionQuery = useQuery({
    queryKey: ["session"],
    queryFn: sessionApi.getSession,
    retry: false,
  });

  useEffect(() => {
    applyUiPreferences(sessionQuery.data?.ui_preferences);
  }, [sessionQuery.data]);

  const loginMutation = useMutation({
    mutationFn: sessionApi.login,
    onSuccess: (data) => {
      queryClient.setQueryData(["session"], data);
      queryClient.invalidateQueries();
    },
  });

  const signupMutation = useMutation({
    mutationFn: sessionApi.signup,
    onSuccess: (data) => {
      queryClient.setQueryData(["session"], data);
      queryClient.invalidateQueries();
    },
  });

  const logoutMutation = useMutation({
    mutationFn: sessionApi.logout,
    onSuccess: async () => {
      queryClient.setQueryData(["session"], null);
      await queryClient.invalidateQueries();
    },
  });

  const value = {
    session: sessionQuery.data,
    user: sessionQuery.data?.user || null,
    uiPreferences: sessionQuery.data?.ui_preferences || null,
    isAuthenticated: Boolean(sessionQuery.data?.user),
    isLoading: sessionQuery.isLoading,
    error: sessionQuery.error,
    refetchSession: sessionQuery.refetch,
    login: loginMutation.mutateAsync,
    signup: signupMutation.mutateAsync,
    logout: logoutMutation.mutateAsync,
    forgotPassword: sessionApi.forgotPassword,
    resetPassword: sessionApi.resetPassword,
    authPending: loginMutation.isPending || signupMutation.isPending || logoutMutation.isPending,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (!context) {
    throw new Error("useAuth must be used within AuthProvider");
  }
  return context;
}
