import { lazy, Suspense } from 'react';
import { createBrowserRouter, Navigate } from 'react-router-dom';
import AppShell from '@/components/AppShell/AppShell';
import RequireAuth from './RequireAuth';
import LoginPage from '@/pages/LoginPage/LoginPage';
import NotFoundPage from '@/pages/NotFoundPage/NotFoundPage';
import DashboardSkeleton from '@/components/Skeleton/DashboardSkeleton';
import AlertTableSkeleton from '@/components/Skeleton/AlertTableSkeleton';
import AlertDetailSkeleton from '@/components/Skeleton/AlertDetailSkeleton';

// Lazy-loaded pages for code splitting
const DashboardPage = lazy(() => import('@/pages/DashboardPage/DashboardPage'));
const AlertsPage = lazy(() => import('@/pages/AlertsPage/AlertsPage'));
const AlertDetailPage = lazy(() => import('@/pages/AlertDetailPage/AlertDetailPage'));
const NetworkPage = lazy(() => import('@/pages/NetworkPage/NetworkPage'));
const ThreatsPage = lazy(() => import('@/pages/ThreatsPage/ThreatsPage'));
const SettingsPage = lazy(() => import('@/pages/SettingsPage/SettingsPage'));

export const router = createBrowserRouter([
  {
    path: '/login',
    element: <LoginPage />,
  },
  {
    path: '/',
    element: (
      <RequireAuth>
        <AppShell />
      </RequireAuth>
    ),
    children: [
      {
        index: true,
        element: <Navigate to="/dashboard" replace />,
      },
      {
        path: 'dashboard',
        element: <Suspense fallback={<DashboardSkeleton />}><DashboardPage /></Suspense>,
      },
      {
        path: 'alerts',
        element: <Suspense fallback={<AlertTableSkeleton />}><AlertsPage /></Suspense>,
      },
      {
        path: 'alerts/:id',
        element: <Suspense fallback={<AlertDetailSkeleton />}><AlertDetailPage /></Suspense>,
      },
      {
        path: 'network',
        element: <Suspense fallback={<DashboardSkeleton />}><NetworkPage /></Suspense>,
      },
      {
        path: 'threats',
        element: <Suspense fallback={<DashboardSkeleton />}><ThreatsPage /></Suspense>,
      },
      {
        path: 'settings',
        element: <Suspense fallback={<DashboardSkeleton />}><SettingsPage /></Suspense>,
      },
    ],
  },
  {
    path: '*',
    element: <NotFoundPage />,
  },
]);
