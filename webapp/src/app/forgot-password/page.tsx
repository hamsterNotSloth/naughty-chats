'use client'

import { useState, Suspense } from 'react'
import Link from 'next/link'
import { useSearchParams } from 'next/navigation'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'
import { Input } from '@/components/ui/input'
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline'

interface PasswordStrength {
  hasMinLength: boolean
  hasUppercase: boolean
  hasLowercase: boolean
  hasNumber: boolean
  hasSpecialChar: boolean
}

function ForgotPasswordContent() {
  const searchParams = useSearchParams()
  const token = searchParams.get('token')
  const isResetMode = !!token

  const [email, setEmail] = useState('')
  const [newPassword, setNewPassword] = useState('')
  const [confirmPassword, setConfirmPassword] = useState('')
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
  const [isComplete, setIsComplete] = useState(false)
  const [error, setError] = useState('')
  const [passwordStrength, setPasswordStrength] = useState<PasswordStrength>({
    hasMinLength: false,
    hasUppercase: false,
    hasLowercase: false,
    hasNumber: false,
    hasSpecialChar: false
  })

  const checkPasswordStrength = (password: string): PasswordStrength => {
    return {
      hasMinLength: password.length >= 8,
      hasUppercase: /[A-Z]/.test(password),
      hasLowercase: /[a-z]/.test(password),
      hasNumber: /\d/.test(password),
      hasSpecialChar: /[!@#$%^&*(),.?":{}|<>]/.test(password)
    }
  }

  const handlePasswordChange = (password: string) => {
    setNewPassword(password)
    setPasswordStrength(checkPasswordStrength(password))
  }

  const handleRequestReset = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    try {
      // Mock API call for password reset request
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Always show success to prevent email enumeration
      setIsComplete(true)
    } catch {
      setError('An error occurred. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleResetPassword = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')

    // Validation
    if (newPassword !== confirmPassword) {
      setError('Passwords do not match')
      setIsLoading(false)
      return
    }

    const strength = checkPasswordStrength(newPassword)
    const isPasswordStrong = Object.values(strength).every(Boolean)
    
    if (!isPasswordStrong) {
      setError('Password does not meet security requirements')
      setIsLoading(false)
      return
    }

    try {
      // Mock API call for password reset confirmation
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Simulate token validation
      if (token === 'invalid') {
        setError('This reset link has expired or is invalid. Please request a new one.')
        setIsLoading(false)
        return
      }
      
      setIsComplete(true)
    } catch {
      setError('An error occurred. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const isPasswordValid = Object.values(passwordStrength).every(Boolean)

  if (isComplete) {
    return (
      <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
        <div className="max-w-md w-full space-y-8">
          <Card className="bg-gray-800 border-gray-700">
            <CardHeader className="text-center">
              <div className="mx-auto flex items-center justify-center h-12 w-12 rounded-full bg-green-100 mb-4">
                <CheckIcon className="h-6 w-6 text-green-600" />
              </div>
              <CardTitle className="text-2xl text-white">
                {isResetMode ? 'Password Reset Successful' : 'Check Your Email'}
              </CardTitle>
              <CardDescription className="text-gray-400">
                {isResetMode 
                  ? 'Your password has been successfully reset. You can now sign in with your new password.'
                  : 'If an account with that email exists, we\'ve sent you a password reset link.'
                }
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="text-center">
                <Link href="/signin">
                  <Button className="w-full bg-purple-600 hover:bg-purple-700 text-white">
                    {isResetMode ? 'Sign In Now' : 'Back to Sign In'}
                  </Button>
                </Link>
              </div>
            </CardContent>
          </Card>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-white">
            {isResetMode ? 'Reset Your Password' : 'Forgot Your Password?'}
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            {isResetMode 
              ? 'Enter your new password below'
              : 'Enter your email address and we\'ll send you a reset link'
            }
          </p>
        </div>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-white">
              {isResetMode ? 'New Password' : 'Password Reset'}
            </CardTitle>
            <CardDescription className="text-center text-gray-400">
              {isResetMode 
                ? 'Choose a strong password for your account'
                : 'We\'ll send reset instructions to your email'
              }
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {error && (
              <div className="bg-red-900/50 border border-red-600 text-red-200 px-3 py-2 rounded-md text-sm" role="alert">
                {error}
              </div>
            )}

            {isResetMode ? (
              <form onSubmit={handleResetPassword} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="newPassword" className="text-sm font-medium text-gray-300">
                    New Password
                  </label>
                  <div className="relative">
                    <Input
                      id="newPassword"
                      type={showPassword ? "text" : "password"}
                      placeholder="Enter your new password"
                      value={newPassword}
                      onChange={(e) => handlePasswordChange(e.target.value)}
                      className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-purple-500 pr-10"
                      required
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowPassword(!showPassword)}
                    >
                      {showPassword ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                      ) : (
                        <EyeIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                  </div>
                  
                  {/* Password Requirements */}
                  {newPassword && (
                    <div className="text-xs space-y-1">
                      <p className="text-gray-400">Password requirements:</p>
                      <ul className="space-y-1" role="list">
                        <li className={`flex items-center ${passwordStrength.hasMinLength ? 'text-green-400' : 'text-gray-400'}`}>
                          {passwordStrength.hasMinLength ? <CheckIcon className="h-3 w-3 mr-1" /> : <XMarkIcon className="h-3 w-3 mr-1" />}
                          At least 8 characters
                        </li>
                        <li className={`flex items-center ${passwordStrength.hasUppercase ? 'text-green-400' : 'text-gray-400'}`}>
                          {passwordStrength.hasUppercase ? <CheckIcon className="h-3 w-3 mr-1" /> : <XMarkIcon className="h-3 w-3 mr-1" />}
                          One uppercase letter
                        </li>
                        <li className={`flex items-center ${passwordStrength.hasLowercase ? 'text-green-400' : 'text-gray-400'}`}>
                          {passwordStrength.hasLowercase ? <CheckIcon className="h-3 w-3 mr-1" /> : <XMarkIcon className="h-3 w-3 mr-1" />}
                          One lowercase letter
                        </li>
                        <li className={`flex items-center ${passwordStrength.hasNumber ? 'text-green-400' : 'text-gray-400'}`}>
                          {passwordStrength.hasNumber ? <CheckIcon className="h-3 w-3 mr-1" /> : <XMarkIcon className="h-3 w-3 mr-1" />}
                          One number
                        </li>
                        <li className={`flex items-center ${passwordStrength.hasSpecialChar ? 'text-green-400' : 'text-gray-400'}`}>
                          {passwordStrength.hasSpecialChar ? <CheckIcon className="h-3 w-3 mr-1" /> : <XMarkIcon className="h-3 w-3 mr-1" />}
                          One special character
                        </li>
                      </ul>
                    </div>
                  )}
                </div>

                <div className="space-y-2">
                  <label htmlFor="confirmPassword" className="text-sm font-medium text-gray-300">
                    Confirm New Password
                  </label>
                  <div className="relative">
                    <Input
                      id="confirmPassword"
                      type={showConfirmPassword ? "text" : "password"}
                      placeholder="Confirm your new password"
                      value={confirmPassword}
                      onChange={(e) => setConfirmPassword(e.target.value)}
                      className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-purple-500 pr-10"
                      required
                    />
                    <button
                      type="button"
                      className="absolute inset-y-0 right-0 pr-3 flex items-center"
                      onClick={() => setShowConfirmPassword(!showConfirmPassword)}
                    >
                      {showConfirmPassword ? (
                        <EyeSlashIcon className="h-5 w-5 text-gray-400" />
                      ) : (
                        <EyeIcon className="h-5 w-5 text-gray-400" />
                      )}
                    </button>
                  </div>
                  {confirmPassword && newPassword !== confirmPassword && (
                    <p className="text-sm text-red-400">Passwords do not match</p>
                  )}
                </div>

                <Button
                  type="submit"
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                  disabled={isLoading || !isPasswordValid}
                >
                  {isLoading ? 'Resetting Password...' : 'Reset Password'}
                </Button>
              </form>
            ) : (
              <form onSubmit={handleRequestReset} className="space-y-4">
                <div className="space-y-2">
                  <label htmlFor="email" className="text-sm font-medium text-gray-300">
                    Email
                  </label>
                  <Input
                    id="email"
                    type="email"
                    placeholder="Enter your email address"
                    value={email}
                    onChange={(e) => setEmail(e.target.value)}
                    className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-purple-500"
                    required
                  />
                </div>

                <Button
                  type="submit"
                  className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                  disabled={isLoading}
                >
                  {isLoading ? 'Sending Reset Link...' : 'Send Reset Link'}
                </Button>
              </form>
            )}

            <div className="text-center">
              <span className="text-sm text-gray-400">
                Remember your password?{' '}
                <Link href="/signin" className="font-medium text-purple-400 hover:text-purple-300">
                  Sign in
                </Link>
              </span>
            </div>
          </CardContent>
        </Card>
      </div>
    </div>
  )
}

export default function ForgotPasswordPage() {
  return (
    <Suspense fallback={<div>Loading...</div>}>
      <ForgotPasswordContent />
    </Suspense>
  )
}