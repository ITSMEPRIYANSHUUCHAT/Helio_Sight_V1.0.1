import React from 'react';
import {MultiStepRegistration} from './MultiStepRegistration';  // Import MultiStep
import { toast } from 'sonner';

interface RegisterFormProps {
  onToggleAuth: () => void;
}

export const RegisterForm: React.FC<RegisterFormProps> = ({ onToggleAuth }) => {
  const handleRegisterSuccess = (token: string) => {
    localStorage.setItem('token', token);
    toast.success('Registration complete! Welcome to Solar Dashboard ☀️');
    window.location.href = '/dashboard';  // Redirect to dashboard
  };

  return (
    <MultiStepRegistration
      onRegister={handleRegisterSuccess}
      onToggleAuth={onToggleAuth}
    />
  );
};