import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import { AnimatePresence } from 'framer-motion';
import { ThemeProvider } from './context/ThemeContext';
import { AuthProvider, useAuth } from './context/AuthContext';

import Layout from './components/Layout';
import Landing from './pages/Landing';
import Login from './pages/Login';
import Register from './pages/Register';
import Questionnaire from './pages/Questionnaire';
import Profile from './pages/Profile';
import BillAnalysis from './pages/BillAnalysis';
import FindTreatment from './pages/FindTreatment';
import ChatAssistant from './pages/ChatAssistant';
import Settings from './pages/Settings';
import MedicalDeals from './pages/MedicalDeals';
import Fundraisers from './pages/Fundraisers';
import ICUBeds from './pages/ICUBeds';

const ProtectedRoute = ({ children }) => {
  const { isAuthenticated } = useAuth();
  if (!isAuthenticated) return <Navigate to="/login" replace />;
  return children;
};

// Questionnaire: must be logged in AND not yet completed profile
const OnboardingRoute = ({ children }) => {
  const { isAuthenticated, needsOnboarding } = useAuth();
  if (!isAuthenticated) return <Navigate to="/register" replace />;
  if (!needsOnboarding) return <Navigate to="/profile" replace />;
  return children;
};

function AppRoutes() {
  return (
    <Layout>
      <AnimatePresence mode="wait">
        <Routes>
          <Route path="/" element={<Landing />} />
          <Route path="/login" element={<Login />} />
          <Route path="/register" element={<Register />} />
          <Route path="/questionnaire" element={<OnboardingRoute><Questionnaire /></OnboardingRoute>} />
          <Route path="/profile" element={<ProtectedRoute><Profile /></ProtectedRoute>} />
          <Route path="/bill-analysis" element={<ProtectedRoute><BillAnalysis /></ProtectedRoute>} />
          <Route path="/find-treatment" element={<FindTreatment />} />
          <Route path="/assistant" element={<ProtectedRoute><ChatAssistant /></ProtectedRoute>} />
          <Route path="/settings" element={<ProtectedRoute><Settings /></ProtectedRoute>} />
          <Route path="/deals" element={<MedicalDeals />} />
          <Route path="/fundraisers" element={<Fundraisers />} />
          <Route path="/icu-beds" element={<ICUBeds />} />
        </Routes>
      </AnimatePresence>
    </Layout>
  );
}

function App() {
  return (
    <ThemeProvider>
      <AuthProvider>
        <Router>
          <AppRoutes />
        </Router>
      </AuthProvider>
    </ThemeProvider>
  );
}

export default App;
