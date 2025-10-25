import React from 'react';
import { Toaster } from "@/components/ui/toaster";
import { Toaster as Sonner } from "@/components/ui/sonner";
import { TooltipProvider } from "@/components/ui/tooltip";
import { QueryClient, QueryClientProvider } from "@tanstack/react-query";
import { BrowserRouter, Routes, Route, Navigate, useNavigate } from "react-router-dom";
import { AuthProvider, useAuth } from "./contexts/AuthContext";
import Dashboard from "./pages/Dashboard";
import NeighbourhoodComparator from "./pages/NeighbourhoodComparator";
import Analytics from "./pages/Analytics";
import SettingsPage from "./pages/SettingsPage";
import NotFound from "./pages/NotFound";
import { LoginForm } from "./components/auth/LoginForm";
import { MultiStepRegistration } from "./components/auth/MultiStepRegistration";

const queryClient = new QueryClient();

// Protected Route Wrapper
const ProtectedRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  return isAuthenticated ? <>{children}</> : <Navigate to="/login" replace />;
};

// Public Route Wrapper
const PublicRoute: React.FC<{ children: React.ReactNode }> = ({ children }) => {
  const { isAuthenticated, isLoading } = useAuth();
  if (isLoading) return <div className="min-h-screen flex items-center justify-center">Loading...</div>;
  return !isAuthenticated ? <>{children}</> : <Navigate to="/dashboard" replace />;
};

// Login Page Wrapper
const LoginPageWrapper = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleLogin = (token: string) => {  // Fixed: Token only
    login({ id: 'temp', username: 'temp', fullname: 'temp' }, token);  // Mock user for now
    navigate('/dashboard');
  };

  const handleToggle = () => navigate('/register');

  return <LoginForm onLogin={handleLogin} onToggleAuth={handleToggle} />;
};

// Register Page Wrapper
const RegisterPageWrapper = () => {
  const navigate = useNavigate();
  const { login } = useAuth();

  const handleRegister = async (token: string) => {  // Fixed: Token only, async
    login({ id: 'temp', username: 'temp', fullname: 'temp' }, token);  // Mock user for now
    navigate('/dashboard');
  };

  const handleToggle = () => navigate('/login');

  return <MultiStepRegistration onRegister={handleRegister} onToggleAuth={handleToggle} />;
};

const App = () => (
  <QueryClientProvider client={queryClient}>
    <AuthProvider>
      <TooltipProvider>
        <Toaster />
        <Sonner />
        <BrowserRouter>
          <Routes>
            {/* Public Routes */}
            <Route path="/login" element={<PublicRoute><LoginPageWrapper /></PublicRoute>} />
            <Route path="/register" element={<PublicRoute><RegisterPageWrapper /></PublicRoute>} />
            {/* Protected Routes */}
            <Route path="/" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/dashboard" element={<ProtectedRoute><Dashboard /></ProtectedRoute>} />
            <Route path="/neighbourhood" element={<ProtectedRoute><NeighbourhoodComparator /></ProtectedRoute>} />
            <Route path="/analytics" element={<ProtectedRoute><Analytics /></ProtectedRoute>} />
            <Route path="/settings" element={<ProtectedRoute><SettingsPage /></ProtectedRoute>} />
            {/* 404 */}
            <Route path="*" element={<NotFound />} />
          </Routes>
        </BrowserRouter>
      </TooltipProvider>
    </AuthProvider>
  </QueryClientProvider>
);

export default App;