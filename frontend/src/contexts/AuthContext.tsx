/**
 * Mock authentication context.
 *
 * MOCK ONLY — no real JWT, sessions, password hashing, or RBAC.
 * Provides a mock user context for the dummy frontend.
 */

import { createContext, useContext, useState, useCallback } from 'react';
import type { ReactNode } from 'react';
import type { MockUser, MockOrganization } from '../types';
import { MOCK_USER, MOCK_ORG } from '../services/mockData';

interface AuthContextValue {
  isAuthenticated: boolean;
  user: MockUser | null;
  organization: MockOrganization | null;
  isLoading: boolean;
  error: string | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

export function AuthProvider({ children }: { children: ReactNode }) {
  const [isAuthenticated, setIsAuthenticated] = useState(false);
  const [user, setUser] = useState<MockUser | null>(null);
  const [organization, setOrganization] = useState<MockOrganization | null>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const login = useCallback(async (email: string, _password: string) => {
    setIsLoading(true);
    setError(null);

    // Simulate network delay
    await new Promise((r) => setTimeout(r, 800));

    // Mock validation
    if (!email.includes('@')) {
      setError('Invalid email address');
      setIsLoading(false);
      return;
    }

    // Mock success
    setUser(MOCK_USER);
    setOrganization(MOCK_ORG);
    setIsAuthenticated(true);
    setIsLoading(false);
  }, []);

  const logout = useCallback(() => {
    setUser(null);
    setOrganization(null);
    setIsAuthenticated(false);
    setError(null);
  }, []);

  return (
    <AuthContext value={{
      isAuthenticated,
      user,
      organization,
      isLoading,
      error,
      login,
      logout,
    }}>
      {children}
    </AuthContext>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) throw new Error('useAuth must be used within AuthProvider');
  return ctx;
}
