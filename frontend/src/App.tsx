/**
 * Vibhinetra — Root Application Component
 *
 * Wraps the router with the AuthProvider.
 */

import { AuthProvider } from './contexts/AuthContext';
import { ThemeProvider } from './contexts/ThemeContext';
import { NotificationProvider } from './contexts/NotificationContext';
import { AppRouter } from './router';

export default function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <NotificationProvider>
          <AppRouter />
        </NotificationProvider>
      </AuthProvider>
    </ThemeProvider>
  );
}
