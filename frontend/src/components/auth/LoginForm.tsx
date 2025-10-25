import React, { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { User, Lock, Eye, EyeOff, Building, AlertTriangle } from 'lucide-react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Button } from '@/components/ui/button';
import { Label } from '@/components/ui/label';
import { Switch } from '@/components/ui/switch';
import { Alert, AlertDescription } from '@/components/ui/alert';
import { GoogleSignInButton } from './GoogleSignInButton';
import { toast } from 'sonner';
import { apiClient } from '../../utils/api';

interface LoginFormProps {
  onLogin: (token: string) => void;
  onToggleAuth: () => void;
}

export const LoginForm: React.FC<LoginFormProps> = ({ onLogin, onToggleAuth }) => {
  const navigate = useNavigate();
  const [username, setUsername] = useState('');
  const [password, setPassword] = useState('');
  const [showPassword, setShowPassword] = useState(false);
  const [isInstaller, setIsInstaller] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    try {
      const response = await apiClient.login({ username, password, isInstaller });
      localStorage.setItem('token', response.token);   
      onLogin(response.token);
      toast.success('Login Successful! Welcome back! ☀️');
      navigate('/dashboard', { replace: true });;  // Replace to avoid history loop
    } catch (error) {
      console.log('Login error caught, showing funky message');

      const errorMessages = isInstaller
        ? [
          "🔧 Access denied! Your installer credentials seem to be taking a coffee break.",
          "⚡ Oops! Even the best installers sometimes mix up their wires... er, passwords!",
          "🏗️ Construction site closed! Double-check your installer credentials.",
          "🔋 Power down! Your login seems to be running on empty batteries.",
          "🛠️ Tool malfunction! Your login wrench needs some adjusting.",
          "⚙️ Looks like your credentials got tangled in the solar panel cables!"
        ]
        : [
          "☀️ Cloud cover detected! Your login credentials are hiding behind some clouds.",
          "🌅 The sun hasn't risen on your account yet - check those login details!",
          "⚡ Energy levels low! Your username or password needs a solar boost.",
          "🔋 Battery depleted! Time to recharge your login credentials.",
          "🌞 Solar eclipse in progress! Your login seems to be in the shadows.",
          "💡 Lightbulb moment needed! Double-check those glowing credentials!"
        ];

      const randomError = errorMessages[Math.floor(Math.random() * errorMessages.length)];
      setError(randomError);
      toast.error("Login Failed", { description: randomError });
    } finally {
      setIsLoading(false);
    }
  };

  const handleGoogleSignIn = async () => {
    console.log('Google Sign-In clicked - requires implementation');
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-emerald-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <div className={`p-3 rounded-xl w-fit mx-auto mb-4 ${isInstaller ? 'bg-gradient-to-r from-orange-500 to-red-500' : 'bg-gradient-to-r from-blue-500 to-cyan-500'}`}>
            {isInstaller ? <Building className="w-8 h-8 text-white" /> : <User className="w-8 h-8 text-white" />}
          </div>
          <CardTitle className={`text-2xl font-bold bg-clip-text text-transparent ${isInstaller ? 'bg-gradient-to-r from-orange-600 to-red-600' : 'bg-gradient-to-r from-blue-600 to-cyan-600'}`}>
            Solar PV Dashboard
          </CardTitle>
          <p className="text-slate-600">
            {isInstaller ? 'Sign in as installer to manage systems' : 'Sign in to access your solar system'}
          </p>
        </CardHeader>
        <CardContent>
          <div className="flex items-center justify-center space-x-4 mb-6 p-4 bg-slate-50 rounded-lg">
            <span className={`text-sm font-medium ${!isInstaller ? 'text-blue-600' : 'text-slate-500'}`}>
              Customer
            </span>
            <Switch
              checked={isInstaller}
              onCheckedChange={setIsInstaller}
              className="data-[state=checked]:bg-orange-500"
            />
            <span className={`text-sm font-medium ${isInstaller ? 'text-orange-600' : 'text-slate-500'}`}>
              Installer
            </span>
          </div>

          {error && (
            <Alert variant="destructive" className="mb-4 animate-pulse border-2">
              <AlertTriangle className="h-4 w-4" />
              <AlertDescription className="font-medium text-sm">
                {error}
              </AlertDescription>
            </Alert>
          )}

           

          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="space-y-2">
              <Label htmlFor="username">Username</Label>
              <Input
                id="username"
                type="text"
                placeholder="Enter your username"
                value={username}
                onChange={(e) => setUsername(e.target.value)}
                required
                disabled={isLoading}
              />
            </div>

            <div className="space-y-2">
              <Label htmlFor="password">Password</Label>
              <div className="relative">
                <Input
                  id="password"
                  type={showPassword ? 'text' : 'password'}
                  placeholder="Enter your password"
                  value={password}
                  onChange={(e) => setPassword(e.target.value)}
                  required
                  disabled={isLoading}
                />
                <button
                  type="button"
                  onClick={() => setShowPassword(!showPassword)}
                  className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-500 hover:text-gray-700 transition-colors"
                  disabled={isLoading}
                  tabIndex={-1}
                >
                  {showPassword ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            <Button
              type="submit"
              className={`w-full ${isInstaller ? 'bg-gradient-to-r from-orange-500 to-red-500 hover:from-orange-600 hover:to-red-600' : 'bg-gradient-to-r from-blue-500 to-cyan-500 hover:from-blue-600 hover:to-cyan-600'}`}
              disabled={isLoading}
            >
              {isLoading ? 'Signing In...' : `Sign In as ${isInstaller ? 'Installer' : 'Customer'}`}
            </Button>
          </form>

          <div className="mt-4">
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-white px-2 text-muted-foreground">Or continue with</span>
              </div>
            </div>

            <GoogleSignInButton onClick={handleGoogleSignIn} className="mt-4" />
          </div>

          <div className="mt-4 text-center">
            <button
              onClick={onToggleAuth}
              className={`text-sm hover:underline ${isInstaller ? 'text-orange-600' : 'text-blue-600'}`}
            >
              Don't have an account? Sign up
            </button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};