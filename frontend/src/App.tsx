import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { useEffect } from 'react';
import { Toaster } from 'react-hot-toast';
import { useAuthStore } from '@/store/authStore';
import { useBackendStore } from '@/store/backendStore';
import { MainLayout } from '@/components/layout/MainLayout';
import { LoginPage } from '@/pages/LoginPage';
import { SignupPage } from '@/pages/SignupPage';
import { Dashboard } from '@/pages/Dashboard';
import { SettingsPage } from '@/pages/SettingsPage';
import { ChatPage } from '@/pages/ChatPage';
import { ChannelsPage } from '@/pages/ChannelsPage';
import { ModelsPage } from '@/pages/ModelsPage';
import { AgentsPage } from '@/pages/AgentsPage';
import { TasksPage } from '@/pages/TasksPage';
import { MonitoringPage } from '@/pages/MonitoringPage';
import { ConstitutionPage } from '@/pages/ConstitutionPage';
import { SovereignDashboard } from '@/pages/SovereignDashboard';

export default function App() {
  const { user, checkAuth } = useAuthStore();
  const { startPolling, stopPolling } = useBackendStore();

  // Check authentication on mount
  useEffect(() => {
    checkAuth();
  }, [checkAuth]);

  // Start backend health polling when app loads
  useEffect(() => {
    startPolling();
    return () => stopPolling();
  }, [startPolling, stopPolling]);

  return (
    <Router>
      <Toaster
        position="top-right"
        toastOptions={{
          duration: 4000,
          className: 'dark:bg-gray-800 dark:text-white',
          style: {
            background: '#1f2937',
            color: '#fff',
          },
        }}
      />

      <Routes>
        {/* Public Routes */}
        <Route
          path="/login"
          element={!user?.isAuthenticated ? <LoginPage /> : <Navigate to="/" replace />}
        />
        <Route
          path="/signup"
          element={!user?.isAuthenticated ? <SignupPage /> : <Navigate to="/" replace />}
        />

        {/* Protected Routes - All require authentication */}
        <Route
          path="/"
          element={
            user?.isAuthenticated ? (
              <MainLayout />
            ) : (
              <Navigate to="/login" replace />
            )
          }
        >
          {/* Dashboard - Default landing page */}
          <Route index element={<Dashboard />} />

          {/* Main Features */}
          <Route path="chat" element={<ChatPage />} />
          <Route path="agents" element={<AgentsPage />} />
          <Route path="tasks" element={<TasksPage />} />
          <Route path="monitoring" element={<MonitoringPage />} />

          {/* Configuration */}
          <Route path="constitution" element={<ConstitutionPage />} />
          <Route path="models" element={<ModelsPage />} />
          <Route path="channels" element={<ChannelsPage />} />

          {/* Sovereign-Only Dashboard - Access control handled inside component */}
          <Route path="sovereign" element={<SovereignDashboard />} />

          {/* Settings */}
          <Route path="settings" element={<SettingsPage />} />
        </Route>

        {/* Catch-all redirect */}
        <Route path="*" element={<Navigate to="/" replace />} />
      </Routes>
    </Router>
  );
}