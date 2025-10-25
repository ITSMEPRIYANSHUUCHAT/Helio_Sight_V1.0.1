import React, { useState, useRef, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/card';
import { Button } from '@/components/ui/button';
import { Input } from '@/components/ui/input';
import { toast } from 'sonner';
import { AlertTriangle, RefreshCw } from 'lucide-react';

interface OTPVerificationProps {
  email: string;
  onVerify: (otp: string) => void;
  onBack: () => void;
  onResend: () => void;
}

export const OTPVerification: React.FC<OTPVerificationProps> = ({ email, onVerify, onBack, onResend }) => {
  const [otp, setOtp] = useState(['', '', '', '', '', '']); // 6-digit array
  const [isLoading, setIsLoading] = useState(false);
  const inputsRef = useRef<(HTMLInputElement | null)[]>([]);

  useEffect(() => {
    // Focus first input on mount
    inputsRef.current[0]?.focus();
  }, []);

  const handleInputChange = (index: number, value: string) => {
    // Ensure only numeric
    const numericValue = value.replace(/[^0-9]/g, '');  // Strip non-digits
    if (numericValue.length > 1) return; // Single digit only
    const newOtp = [...otp];
    newOtp[index] = numericValue;
    setOtp(newOtp);
    if (numericValue && index < 5) {
      inputsRef.current[index + 1]?.focus(); // Auto-focus next
    }
  };

  const handleKeyDown = (index: number, e: React.KeyboardEvent) => {
    if (e.key === 'Backspace' && !otp[index] && index > 0) {
      inputsRef.current[index - 1]?.focus(); // Back to previous
    }
    if (e.key === 'Enter') {
      handleSubmit();
    }
  };

  const handleSubmit = async () => {
    const otpString = otp.join(''); // Extract otp string
    console.log('OTP String:', otpString);  // Debug log
    if (otpString.length !== 6) {
      toast.error('Please enter full 6-digit OTP');
      return;
    }
    setIsLoading(true);
    try {
      onVerify(otpString); // Pass otp string to onVerify
    } catch (error) {
      console.error('OTP Verify error:', error);
      toast.error('Verification failed. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  const handleResend = async () => {
    setIsLoading(true);
    try {
      onResend();
    } catch (error) {
      toast.error('Resend failed. Try again.');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-cyan-50 to-emerald-50 flex items-center justify-center p-4">
      <Card className="w-full max-w-md">
        <CardHeader className="text-center">
          <CardTitle className="text-2xl font-bold">Verify Your Email</CardTitle>
          <p className="text-slate-600">
            We've sent a 6-digit code to {email}
          </p>
        </CardHeader>
        <CardContent>
          <div className="space-y-4">
            <div className="flex justify-center space-x-2">
              {otp.map((digit, index) => (
                <Input
                  key={index}
                  ref={(el) => (inputsRef.current[index] = el)}
                  type="text"
                  inputMode="numeric"  // Numeric keyboard
                  pattern="[0-9]*"  // Numeric pattern
                  maxLength={1}
                  value={digit}
                  onChange={(e) => handleInputChange(index, e.target.value)}
                  onKeyDown={(e) => handleKeyDown(index, e)}
                  className="w-12 h-12 text-center text-lg font-mono"
                  disabled={isLoading}
                />
              ))}
            </div>
            <Button onClick={handleSubmit} disabled={isLoading || otp.join('').length !== 6} className="w-full">
              {isLoading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
              Verify Code
            </Button>
            <Button variant="outline" onClick={handleResend} disabled={isLoading} className="w-full">
              {isLoading ? <RefreshCw className="mr-2 h-4 w-4 animate-spin" /> : null}
              Resend Code
            </Button>
            <Button variant="ghost" onClick={onBack} className="w-full">
              Back to Registration
            </Button>
          </div>
        </CardContent>
      </Card>
    </div>
  );
};