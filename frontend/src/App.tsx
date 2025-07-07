import React from 'react';
import { BrowserRouter as Router, Routes, Route } from 'react-router-dom';
import Layout from '@/components/Layout';
import Dashboard from '@/pages/Dashboard';
import EarningsCalendar from '@/pages/EarningsCalendar';
import CompanyProfile from '@/pages/CompanyProfile';
import Predictions from '@/pages/Predictions';
import AgentChat from '@/pages/AgentChat';
import Analytics from '@/pages/Analytics';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/earnings" element={<EarningsCalendar />} />
          <Route path="/company/:symbol" element={<CompanyProfile />} />
          <Route path="/predictions" element={<Predictions />} />
          <Route path="/chat" element={<AgentChat />} />
          <Route path="/analytics" element={<Analytics />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;