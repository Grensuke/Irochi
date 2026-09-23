import React, { createContext, useContext, useState, useCallback, useEffect, useRef } from 'react';
import type { User } from '@/types';

interface AuthContextValue {
  user: User | null;
  role: 'ANALYST' | 'ADMIN' | null;
  isAuthenticated: boolean;
  login: (username: string, password: string) => Promise<void>;
  logout: () => void;
}

const AuthContext = createContext<AuthContextValue | null>(null);

// ─── Mock credentials ───
const MOCK_USERS: Record<string, { password: string; user: User }> = {
  analyst: {
    password: 'analyst123',
    user: {
      id: 'usr_001',
      username: 'analyst',
      role: 'ANALYST',
      displayName: 'Sarah Chen',
      initials: 'SC',
    },
  },
  admin: {
    password: 'admin123',
    user: {
      id: 'usr_002',
      username: 'admin',
      role: 'ADMIN',
      displayName: 'Alex Morgan',
      initials: 'AM',
    },
  },
};

// ─── Mock JWT generation ───
function createMockJWT(user: User): string {
  const header = btoa(JSON.stringify({ alg: 'HS256', typ: 'JWT' }));
  const payload = btoa(
    JSON.stringify({
      sub: user.id,
      username: user.username,
      role: user.role,
      iat: Math.floor(Date.now() / 1000),
      exp: Math.floor(Date.now() / 1000) + 3600, // 1h
    })
  );
  const signature = btoa('mock-signature');
  return `${header}.${payload}.${signature}`;
}

function decodeJWT(token: string): { exp: number; sub: string; username: string; role: string } | null {
  try {
    const parts = token.split('.');
    if (parts.length !== 3) return null;
    return JSON.parse(atob(parts[1]));
  } catch {
    return null;
  }
}

const REFRESH_KEY = 'sih-refresh';

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [token, setToken] = useState<string | null>(null);
  const refreshTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  // ─── Try restore session from refresh token ───
  useEffect(() => {
    try {
      const refreshData = localStorage.getItem(REFRESH_KEY);
      if (refreshData) {
        const parsed = JSON.parse(refreshData);
        const mockUser = Object.values(MOCK_USERS).find(m => m.user.id === parsed.userId);
        if (mockUser) {
          const newToken = createMockJWT(mockUser.user);
          setUser(mockUser.user);
          setToken(newToken);
          scheduleRefresh(newToken, mockUser.user);
        }
      }
    } catch {
      // no valid refresh token
    }
  }, []); // eslint-disable-line react-hooks/exhaustive-deps

  const scheduleRefresh = useCallback((jwt: string, currentUser: User) => {
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    const decoded = decodeJWT(jwt);
    if (!decoded) return;

    // Refresh 60s before expiry
    const expiresIn = decoded.exp * 1000 - Date.now();
    const refreshIn = Math.max(expiresIn - 60000, 5000);

    refreshTimerRef.current = setTimeout(() => {
      const newToken = createMockJWT(currentUser);
      setToken(newToken);
      scheduleRefresh(newToken, currentUser);
    }, refreshIn);
  }, []);

  const login = useCallback(async (username: string, password: string): Promise<void> => {
    // Simulate network latency
    await new Promise(resolve => setTimeout(resolve, 800 + Math.random() * 400));

    const entry = MOCK_USERS[username.toLowerCase()];
    if (!entry || entry.password !== password) {
      throw new Error('Invalid credentials. Access denied.');
    }

    const jwt = createMockJWT(entry.user);
    setUser(entry.user);
    setToken(jwt);

    // Store refresh token (mock)
    try {
      localStorage.setItem(
        REFRESH_KEY,
        JSON.stringify({ userId: entry.user.id, token: 'mock-refresh-' + Date.now() })
      );
    } catch {
      // localStorage unavailable
    }

    scheduleRefresh(jwt, entry.user);
  }, [scheduleRefresh]);

  const logout = useCallback(() => {
    setUser(null);
    setToken(null);
    if (refreshTimerRef.current) {
      clearTimeout(refreshTimerRef.current);
    }
    try {
      localStorage.removeItem(REFRESH_KEY);
    } catch {
      // localStorage unavailable
    }
  }, []);

  return (
    <AuthContext.Provider
      value={{
        user,
        role: user?.role ?? null,
        isAuthenticated: !!token && !!user,
        login,
        logout,
      }}
    >
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth(): AuthContextValue {
  const ctx = useContext(AuthContext);
  if (!ctx) {
    throw new Error('useAuth must be used within <AuthProvider>');
  }
  return ctx;
}

export default AuthContext;
