import React from 'react';
import { BrowserRouter, Routes, Route, Navigate } from 'react-router-dom';
import { AuthProvider } from './context/AuthContext';
import ProtectedRoute from './components/ProtectedRoute';
import LandingPage from './pages/LandingPage';
import LoginPage from './pages/LoginPage';
import RegisterPage from './pages/RegisterPage';
import DashboardPage from './pages/DashboardPage';
import ScannerPage from './pages/ScannerPage';
import ResultsPage from './pages/ResultsPage';
import CropPage from './pages/CropPage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route path="/dashboard" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/scanner" element={<ProtectedRoute><ScannerPage /></ProtectedRoute>} />
          <Route path="/results" element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
          <Route path="/crop" element={<ProtectedRoute><CropPage /></ProtectedRoute>} />

          {/* Placeholder routes — replaced in later phases */}
          <Route path="/fertilizer" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/irrigation" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/weather" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/chatbot" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/market" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/reports" element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}