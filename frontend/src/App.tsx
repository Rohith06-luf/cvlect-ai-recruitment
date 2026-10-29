import React from 'react';
import { BrowserRouter, Routes, Route, Navigate, useLocation } from 'react-router-dom';
import { AuthProvider, useAuth } from './contexts/AuthContext';
import { ToastProvider } from './components/ui/Toast';
import { Layout } from './components/layout/Layout';

// Pages
import { Landing } from './pages/Landing';
import { Login } from './pages/Login';
import { Register } from './pages/Register';

// Candidate Pages
import { CandidateDashboard } from './pages/candidate/Dashboard';
import { ResumeUpload } from './pages/candidate/ResumeUpload';
import { JobBrowser } from './pages/candidate/JobBrowser';
import { JobDetail } from './pages/candidate/JobDetail';
import { Applications } from './pages/candidate/Applications';
import { AskAI } from './pages/candidate/AskAI';

// Recruiter Pages
import { RecruiterDashboard } from './pages/recruiter/Dashboard';
import { JobManagement } from './pages/recruiter/JobManagement';
import { CreateJob } from './pages/recruiter/CreateJob';
import { CandidateSearch } from './pages/recruiter/CandidateSearch';

// Protected Route Guard
const ProtectedRoute: React.FC<{
  children: React.ReactNode;
  allowedRoles?: Array<'candidate' | 'recruiter'>;
}> = ({ children, allowedRoles }) => {
  const { user, isAuthenticated, isLoading } = useAuth();
  const location = useLocation();

  if (isLoading) {
    return (
      <div className="min-h-screen bg-[#0a0e1a] flex items-center justify-center">
        <div className="flex flex-col items-center gap-3">
          <div className="w-10 h-10 border-2 border-violet-500 border-t-transparent rounded-full animate-spin" />
          <span className="text-xs font-semibold text-violet-300">Loading CVlect AI...</span>
        </div>
      </div>
    );
  }

  if (!isAuthenticated) {
    return <Navigate to="/login" state={{ from: location }} replace />;
  }

  if (allowedRoles && user && !allowedRoles.includes(user.role)) {
    return <Navigate to={user.role === 'recruiter' ? '/recruiter/dashboard' : '/candidate/dashboard'} replace />;
  }

  return <>{children}</>;
};

// Root Router
export const App: React.FC = () => {
  return (
    <BrowserRouter>
      <AuthProvider>
        <ToastProvider>
          <Routes>
            {/* Public Routes */}
            <Route path="/" element={<Landing />} />
            <Route path="/login" element={<Login />} />
            <Route path="/register" element={<Register />} />

            {/* Authenticated Application Shell */}
            <Route
              element={
                <ProtectedRoute>
                  <Layout />
                </ProtectedRoute>
              }
            >
              {/* Candidate Routes */}
              <Route
                path="/candidate/dashboard"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <CandidateDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidate/resume"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <ResumeUpload />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidate/jobs"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <JobBrowser />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidate/jobs/:id"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <JobDetail />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidate/applications"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <Applications />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/candidate/assistant"
                element={
                  <ProtectedRoute allowedRoles={['candidate']}>
                    <AskAI />
                  </ProtectedRoute>
                }
              />

              {/* Recruiter Routes */}
              <Route
                path="/recruiter/dashboard"
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <RecruiterDashboard />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recruiter/jobs"
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <JobManagement />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recruiter/jobs/create"
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <CreateJob />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recruiter/candidates"
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <CandidateSearch />
                  </ProtectedRoute>
                }
              />
              <Route
                path="/recruiter/assistant"
                element={
                  <ProtectedRoute allowedRoles={['recruiter']}>
                    <AskAI />
                  </ProtectedRoute>
                }
              />
            </Route>

            {/* Fallback */}
            <Route path="*" element={<Navigate to="/" replace />} />
          </Routes>
        </ToastProvider>
      </AuthProvider>
    </BrowserRouter>
  );
};

export default App;
