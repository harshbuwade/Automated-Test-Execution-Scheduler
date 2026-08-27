import React from 'react';
import { BrowserRouter, Navigate, Route, Routes } from 'react-router-dom';
import { ProtectedRoute } from './components/ProtectedRoute';
import { AuthProvider } from './hooks/useAuth';
import { SidebarLayout } from './layouts/SidebarLayout';
import { DashboardPage } from './pages/DashboardPage';
import { ExecutionDetailsPage } from './pages/ExecutionDetailsPage';
import { ExecutionsPage } from './pages/ExecutionsPage';
import { SchedulesPage } from './pages/SchedulesPage';
import { TestsPage } from './pages/TestsPage';

export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Main Application Layout & Dashboard Routes */}
          <Route
            path="/"
            element={
              <ProtectedRoute>
                <SidebarLayout />
              </ProtectedRoute>
            }
          >
            <Route index element={<DashboardPage />} />
            <Route path="tests" element={<TestsPage />} />
            <Route path="schedules" element={<SchedulesPage />} />
            <Route path="executions" element={<ExecutionsPage />} />
            <Route path="executions/:id" element={<ExecutionDetailsPage />} />
          </Route>

          {/* Catch-all redirect */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
