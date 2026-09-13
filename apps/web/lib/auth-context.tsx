"use client";

import React, { createContext, useContext, useEffect, useState } from "react";
import { useQueryClient } from "@tanstack/react-query";
import { useRouter } from "next/navigation";
import { authApi, setAuthToken, type User } from "./api";

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  isAuthenticated: boolean;
  login: (token: string) => Promise<void>;
  logout: () => void;
  refreshUser: () => Promise<void>;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const router = useRouter();
  const queryClient = useQueryClient();
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  // Initialize auth state on mount
  useEffect(() => {
    initializeAuth();
  }, []);

  const initializeAuth = async () => {
    const token = localStorage.getItem("raglens_token");
    if (!token) {
      setIsLoading(false);
      return;
    }

    try {
      setAuthToken(token);
      const userData = await authApi.me();
      setUser(userData);
    } catch (error) {
      // Token is invalid or expired
      console.error("Failed to restore session:", error);
      localStorage.removeItem("raglens_token");
      setAuthToken(null);
    } finally {
      setIsLoading(false);
    }
  };

  const login = async (token: string) => {
    await queryClient.cancelQueries();
    queryClient.clear();
    localStorage.setItem("raglens_token", token);
    setAuthToken(token);
    
    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch (error) {
      localStorage.removeItem("raglens_token");
      setAuthToken(null);
      setUser(null);
      console.error("Failed to fetch user data:", error);
      throw error;
    }
  };

  const logout = () => {
    localStorage.removeItem("raglens_token");
    setAuthToken(null);
    setUser(null);
    queryClient.cancelQueries().then(() => queryClient.clear());
    router.push("/login");
  };

  const refreshUser = async () => {
    try {
      const userData = await authApi.me();
      setUser(userData);
    } catch (error) {
      console.error("Failed to refresh user data:", error);
      // If refresh fails, log out
      logout();
    }
  };

  const value: AuthContextType = {
    user,
    isLoading,
    isAuthenticated: !!user,
    login,
    logout,
    refreshUser,
  };

  return <AuthContext.Provider value={value}>{children}</AuthContext.Provider>;
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error("useAuth must be used within an AuthProvider");
  }
  return context;
}
