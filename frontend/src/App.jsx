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
import FertilizerPage from './pages/FertilizerPage';
import IrrigationPage from './pages/IrrigationPage';
import WeatherPage from './pages/WeatherPage';
import ChatbotPage from './pages/ChatbotPage';
import MarketPage from './pages/MarketPage';
import ReportsPage from './pages/ReportsPage';
import AdminPage from './pages/AdminPage';
import ProfilePage from './pages/ProfilePage';

export default function App() {
  return (
    <BrowserRouter>
      <AuthProvider>
        <Routes>
          <Route path="/" element={<LandingPage />} />
          <Route path="/login" element={<LoginPage />} />
          <Route path="/register" element={<RegisterPage />} />

          <Route path="/dashboard"       element={<ProtectedRoute><DashboardPage /></ProtectedRoute>} />
          <Route path="/scanner"         element={<ProtectedRoute><ScannerPage /></ProtectedRoute>} />
          <Route path="/results"         element={<ProtectedRoute><ResultsPage /></ProtectedRoute>} />
          <Route path="/crop"            element={<ProtectedRoute><CropPage /></ProtectedRoute>} />
          <Route path="/fertilizer"      element={<ProtectedRoute><FertilizerPage /></ProtectedRoute>} />
          <Route path="/irrigation"      element={<ProtectedRoute><IrrigationPage /></ProtectedRoute>} />
          <Route path="/weather"         element={<ProtectedRoute><WeatherPage /></ProtectedRoute>} />
          <Route path="/chatbot"         element={<ProtectedRoute><ChatbotPage /></ProtectedRoute>} />
          <Route path="/market"          element={<ProtectedRoute><MarketPage /></ProtectedRoute>} />
          <Route path="/reports"         element={<ProtectedRoute><ReportsPage /></ProtectedRoute>} />
          <Route path="/profile"         element={<ProtectedRoute><ProfilePage /></ProtectedRoute>} />
          <Route path="/admin-dashboard" element={<ProtectedRoute><AdminPage /></ProtectedRoute>} />

          <Route path="*" element={<Navigate to="/" replace />} />
        </Routes>
      </AuthProvider>
    </BrowserRouter>
  );
}