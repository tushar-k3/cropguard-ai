import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          {/* Public routes */}
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          {/* Protected routes — redirect to /login if not authenticated */}
          <Route
            path="/dashboard"
            element={
              <ProtectedRoute>
                <DashboardPage />
              </ProtectedRoute>
            }
          />

          {/* Placeholder routes for future phases — show dashboard for now */}
          <Route path="/scanner" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/crop" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/fertilizer" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/irrigation" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/weather" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/chatbot" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/market" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />

          {/* Catch-all — redirect unknown routes to home */}
          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}