import React, { useState, useEffect } from 'react';
import { LoginForm } from '@/components/auth/LoginForm';
import { RegisterForm } from '@/components/auth/RegisterForm';
import { PlantsOverview } from '@/components/plants/PlantsOverview';
import { DeviceDetail } from '@/components/devices/DeviceDetail';
import { DashboardLayout } from '@/components/layout/DashboardLayout';
import UserGuide from '@/components/onboarding/UserGuide';
import { toast } from 'sonner';
import { apiClient } from '@/utils/api';
import { useAuth } from '@/contexts/AuthContext';
import { Device } from '@/types/device';

type ViewState = 'login' | 'register' | 'plants' | 'device';

const Dashboard = () => {
  const { user, isAuthenticated, login, logout, isLoading, setIsAuthenticated } = useAuth();
  const [currentView, setCurrentView] = useState<ViewState>('login');
  const [isLogin, setIsLogin] = useState(true);
  const [selectedDevice, setSelectedDevice] = useState<Device | null>(null);
  const [showUserGuide, setShowUserGuide] = useState(false);

  // Initialize currentView based on localStorage token (before useEffect)
  useEffect(() => {
    const storedToken = localStorage.getItem('token');
    if (storedToken && !isLoading) {
      setCurrentView('plants');
      setIsAuthenticated(true);  // Force authenticated if token exists
    } else if (!isLoading) {
      setCurrentView('login');
    }
  }, [isLoading, setIsAuthenticated]);

  // Auto-navigate to plants if user is authenticated (after init)
  useEffect(() => {
    if (isAuthenticated && user && !isLoading) {
      setCurrentView('plants');
      // Show user guide on first login
      const hasSeenGuide = localStorage.getItem('hasSeenGuide');
      if (!hasSeenGuide) {
        setShowUserGuide(true);
        localStorage.setItem('hasSeenGuide', 'true');
      }
    } else if (!isLoading && !localStorage.getItem('token')) {  // Only login if no token
      setCurrentView('login');
    }
  }, [isAuthenticated, user, isLoading]);

  const handleLogin = (token: string) => {
    setIsAuthenticated(true);  // Explicit set
    toast.success('Welcome to the Solar PV Dashboard demo!');
    setTimeout(() => {  // Delay for state sync
      setCurrentView('plants');
    }, 100);
  };

  const handleRegister = async (userData: { username: string; fullname: string; password: string; confirmPassword: string; isInstaller: boolean }) => {
    try {
      console.log('Register attempt:', userData.fullname, userData.username);
      const response = await apiClient.register(userData);
      
      login(response.user, response.token);
      setCurrentView('plants');
      toast.success(`Welcome, ${response.user.fullname}! Account created successfully.`);
    } catch (error) {
      console.error('Registration failed:', error);
      toast.error('Registration failed. Please try again.');
    }
  };

  const handleLogout = async () => {
    try {
      await apiClient.logout();
      logout();
      setSelectedDevice(null);
      setCurrentView('login');
      setIsLogin(true);
      toast.info('Logged out successfully');
    } catch (error) {
      console.error('Logout error:', error);
      // Still log out locally even if API call fails
      logout();
      setSelectedDevice(null);
      setCurrentView('login');
      setIsLogin(true);
    }
  };

  const handleDeviceSelect = (device: Device) => {
    setSelectedDevice(device);
    setCurrentView('device');
  };

  const handleBackToPlants = () => {
    setSelectedDevice(null);
    setCurrentView('plants');
  };

  const toggleAuthMode = () => {
    setIsLogin(!isLogin);
    setCurrentView(isLogin ? 'register' : 'login');
  };

  const handleCloseUserGuide = () => {
    setShowUserGuide(false);
  };

  if (isLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-emerald-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-500 mx-auto mb-4"></div>
          <p className="text-slate-600">Loading...</p>
        </div>
      </div>
    );
  }

  // Render based on current view state
  if (currentView === 'login') {
    return (
      <LoginForm 
        onLogin={handleLogin} 
        onToggleAuth={toggleAuthMode}
      />
    );
  }

  if (currentView === 'register') {
    return (
      <RegisterForm 
        onToggleAuth={toggleAuthMode}
      />
    );
  }

  if (currentView === 'plants' && user) {
    return (
      <DashboardLayout onLogout={handleLogout}>
        <PlantsOverview 
          user={user}
          onDeviceSelect={handleDeviceSelect}
          onLogout={handleLogout}
        />
        <UserGuide 
          isOpen={showUserGuide} 
          onClose={handleCloseUserGuide} 
        />
      </DashboardLayout>
    );
  }

  if (currentView === 'device' && selectedDevice) {
    return (
      <DashboardLayout onLogout={handleLogout}>
        <DeviceDetail 
          device={selectedDevice}
          onBack={handleBackToPlants}
        />
        <UserGuide 
          isOpen={showUserGuide} 
          onClose={handleCloseUserGuide} 
        />
      </DashboardLayout>
    );
  }

  // Fallback to login if something goes wrong
  return (
    <LoginForm 
      onLogin={handleLogin} 
      onToggleAuth={toggleAuthMode}
    />
  );
};

export default Dashboard;