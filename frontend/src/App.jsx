import React from 'react';
import { BrowserRouter, Routes, Route } from 'react-router-dom';
import LandingPage from './pages/LandingPage';

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<LandingPage />} />
        {/* Phase 2: Login, Register, Dashboard */}
        {/* Phase 3: Plant Scanner, Disease Results */}
        {/* Phase 4: Crop Recommendation */}
        {/* Phase 5: Fertilizer Recommendation */}
        {/* Phase 6: Irrigation Recommendation */}
        {/* Phase 7: Chatbot */}
        {/* Phase 8: Weather Dashboard */}
        {/* Phase 9: Market Prices */}
        {/* Phase 10: Reports */}
        {/* Phase 11: Admin Dashboard */}
      </Routes>
    </BrowserRouter>
  );
}