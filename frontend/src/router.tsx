/**
 * Irochi frontend router.
 *
 * Public routes: Landing, Login
 * Protected routes: App shell with all authenticated pages
 */

import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { useAuth } from './contexts/AuthContext';
import { AppLayout } from './layouts/AppLayout';
import { PublicLayout } from './layouts/PublicLayout';
import { Landing } from './pages/Landing';
import { About } from './pages/About';
import { Capabilities } from './pages/Capabilities';
import { Architecture } from './pages/Architecture';
import { Documentation } from './pages/Documentation';
import { Contact } from './pages/Contact';
import { Login } from './pages/Login';
import { Overview } from './pages/Overview';
import { Alerts } from './pages/Alerts';
import { Threats } from './pages/Threats';
import { Network } from './pages/Network';
import { Analytics } from './pages/Analytics';
import { Settings } from './pages/Settings';
import { NotFound } from './pages/NotFound';
import { AccessDenied } from './pages/AccessDenied';
import { AlertDetailPage } from './pages/AlertDetailPage';
import { Traffic } from './pages/Traffic';
import { Investigation } from './pages/Investigation';
import { AIDetection } from './pages/AIDetection';
import type { ReactNode } from 'react';

function ProtectedRoute({ children }: { children: ReactNode }) {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/" replace />;
  return <>{children}</>;
}

export function AppRouter() {
  return (
    <BrowserRouter>
      <Routes>
        {/* Public routes */}
        <Route element={<PublicLayout />}>
          <Route path="/" element={<Landing />} />
          <Route path="/about" element={<About />} />
          <Route path="/capabilities" element={<Capabilities />} />
          <Route path="/architecture" element={<Architecture />} />
          <Route path="/documentation" element={<Documentation />} />
          <Route path="/contact" element={<Contact />} />
        </Route>
        <Route path="/login" element={<Login />} />
        <Route path="/access-denied" element={<AccessDenied />} />

        {/* Protected application routes */}
        <Route
          path="/app"
          element={
            <ProtectedRoute>
              <AppLayout />
            </ProtectedRoute>
          }
        >
          <Route index element={<Overview />} />
          <Route path="alerts" element={<Alerts />} />
          <Route path="alerts/:id" element={<AlertDetailPage />} />
          <Route path="threats" element={<Threats />} />
          <Route path="network" element={<Network />} />
          <Route path="analytics" element={<Analytics />} />
          <Route path="settings" element={<Settings />} />
          <Route path="traffic" element={<Traffic />} />
          <Route path="investigation" element={<Investigation />} />
          <Route path="ai" element={<AIDetection />} />
          <Route path="*" element={<NotFound />} />
        </Route>

        {/* Catch-all */}
        <Route path="*" element={<NotFound />} />
      </Routes>
    </BrowserRouter>
  );
}
