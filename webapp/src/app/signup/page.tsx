'use client'

import { useState } from 'react'
import Link from 'next/link'
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

export default function SignUpPage() {
  const [formData, setFormData] = useState({
    email: '',
    password: '',
    confirmPassword: '',
    birthYear: '',
    agreeTerms: false
  })
  const [showPassword, setShowPassword] = useState(false)
  const [showConfirmPassword, setShowConfirmPassword] = useState(false)
  const [isLoading, setIsLoading] = useState(false)
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
    setFormData({...formData, password})
    setPasswordStrength(checkPasswordStrength(password))
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsLoading(true)
    setError('')
    
    // Validation
    const currentYear = new Date().getFullYear()
    const age = currentYear - parseInt(formData.birthYear)
    
    if (age < 18) {
      setError('You must be 18 or older to create an account')
      setIsLoading(false)
      return
    }

    if (formData.password !== formData.confirmPassword) {
      setError('Passwords do not match')
      setIsLoading(false)
      return
    }

    const strength = checkPasswordStrength(formData.password)
    const isPasswordStrong = Object.values(strength).every(Boolean)
    
    if (!isPasswordStrong) {
      setError('Password does not meet security requirements')
      setIsLoading(false)
      return
    }

    if (!formData.agreeTerms) {
      setError('You must agree to the Terms of Service and Privacy Policy')
      setIsLoading(false)
      return
    }

    // Mock registration - would connect to actual API
    try {
      // Simulate API call
      await new Promise(resolve => setTimeout(resolve, 1500))
      
      // Success - would redirect and show email verification
      alert('Account created successfully! Check your email for verification.')
    } catch (err) {
      setError('An error occurred. Please try again.')
    } finally {
      setIsLoading(false)
    }
  }

  const handleSocialSignup = (provider: string) => {
    // Mock social signup
    alert(`${provider} signup would open OAuth flow`)
  }

  const isPasswordValid = Object.values(passwordStrength).every(Boolean)

  return (
    <div className="min-h-screen bg-gray-900 flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        <div className="text-center">
          <h2 className="mt-6 text-3xl font-bold text-white">
            Join NaughtyChats
          </h2>
          <p className="mt-2 text-sm text-gray-400">
            Create your account and start exploring amazing AI characters
          </p>
        </div>

        <Card className="bg-gray-800 border-gray-700">
          <CardHeader className="space-y-1">
            <CardTitle className="text-2xl text-center text-white">Sign Up</CardTitle>
            <CardDescription className="text-center text-gray-400">
              Get started with your free account and 100 bonus gems
            </CardDescription>
          </CardHeader>
          <CardContent className="space-y-4">
            {/* Social Signup Buttons */}
            <div className="grid grid-cols-2 gap-3">
              <Button
                variant="outline"
                onClick={() => handleSocialSignup('Google')}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24">
                  <path fill="currentColor" d="M22.56 12.25c0-.78-.07-1.53-.2-2.25H12v4.26h5.92c-.26 1.37-1.04 2.53-2.21 3.31v2.77h3.57c2.08-1.92 3.28-4.74 3.28-8.09z"/>
                  <path fill="currentColor" d="M12 23c2.97 0 5.46-.98 7.28-2.66l-3.57-2.77c-.98.66-2.23 1.06-3.71 1.06-2.86 0-5.29-1.93-6.16-4.53H2.18v2.84C3.99 20.53 7.7 23 12 23z"/>
                  <path fill="currentColor" d="M5.84 14.09c-.22-.66-.35-1.36-.35-2.09s.13-1.43.35-2.09V7.07H2.18C1.43 8.55 1 10.22 1 12s.43 3.45 1.18 4.93l2.85-2.22.81-.62z"/>
                  <path fill="currentColor" d="M12 5.38c1.62 0 3.06.56 4.21 1.64l3.15-3.15C17.45 2.09 14.97 1 12 1 7.7 1 3.99 3.47 2.18 7.07l3.66 2.84c.87-2.6 3.3-4.53 6.16-4.53z"/>
                </svg>
                Google
              </Button>
              <Button
                variant="outline"
                onClick={() => handleSocialSignup('Discord')}
                className="border-gray-600 text-gray-300 hover:bg-gray-700"
              >
                <svg className="w-5 h-5 mr-2" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M20.317 4.37a19.791 19.791 0 0 0-4.885-1.515a.074.074 0 0 0-.079.037c-.21.375-.444.864-.608 1.25a18.27 18.27 0 0 0-5.487 0a12.64 12.64 0 0 0-.617-1.25a.077.077 0 0 0-.079-.037A19.736 19.736 0 0 0 3.677 4.37a.07.07 0 0 0-.032.027C.533 9.046-.32 13.58.099 18.057a.082.082 0 0 0 .031.057a19.9 19.9 0 0 0 5.993 3.03a.078.078 0 0 0 .084-.028a14.09 14.09 0 0 0 1.226-1.994a.076.076 0 0 0-.041-.106a13.107 13.107 0 0 1-1.872-.892a.077.077 0 0 1-.008-.128a10.2 10.2 0 0 0 .372-.292a.074.074 0 0 1 .077-.01c3.928 1.793 8.18 1.793 12.062 0a.074.074 0 0 1 .078.01c.12.098.246.198.373.292a.077.077 0 0 1-.006.127a12.299 12.299 0 0 1-1.873.892a.077.077 0 0 0-.041.107c.36.698.772 1.362 1.225 1.993a.076.076 0 0 0 .084.028a19.839 19.839 0 0 0 6.002-3.03a.077.077 0 0 0 .032-.054c.5-5.177-.838-9.674-3.549-13.66a.061.061 0 0 0-.031-.03zM8.02 15.33c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.956-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.956 2.418-2.157 2.418zm7.975 0c-1.183 0-2.157-1.085-2.157-2.419c0-1.333.955-2.419 2.157-2.419c1.21 0 2.176 1.096 2.157 2.42c0 1.333-.946 2.418-2.157 2.418z"/>
                </svg>
                Discord
              </Button>
            </div>

            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t border-gray-600" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-gray-800 px-2 text-gray-400">Or continue with</span>
              </div>
            </div>

            {/* Registration Form */}
            <form onSubmit={handleSubmit} className="space-y-4">
              {error && (
                <div className="bg-red-900/50 border border-red-600 text-red-200 px-3 py-2 rounded-md text-sm" role="alert">
                  {error}
                </div>
              )}

              <div className="space-y-2">
                <label htmlFor="email" className="text-sm font-medium text-gray-300">
                  Email
                </label>
                <Input
                  id="email"
                  type="email"
                  placeholder="Enter your email"
                  value={formData.email}
                  onChange={(e) => setFormData({...formData, email: e.target.value})}
                  className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-purple-500"
                  required
                />
              </div>

              <div className="space-y-2">
                <label htmlFor="password" className="text-sm font-medium text-gray-300">
                  Password
                </label>
                <div className="relative">
                  <Input
                    id="password"
                    type={showPassword ? "text" : "password"}
                    placeholder="Create a password"
                    value={formData.password}
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
                {formData.password && (
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
                  Confirm Password
                </label>
                <div className="relative">
                  <Input
                    id="confirmPassword"
                    type={showConfirmPassword ? "text" : "password"}
                    placeholder="Confirm your password"
                    value={formData.confirmPassword}
                    onChange={(e) => setFormData({...formData, confirmPassword: e.target.value})}
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
                {formData.confirmPassword && formData.password !== formData.confirmPassword && (
                  <p className="text-sm text-red-400">Passwords do not match</p>
                )}
              </div>

              <div className="space-y-2">
                <label htmlFor="birthYear" className="text-sm font-medium text-gray-300">
                  Birth Year
                </label>
                <Input
                  id="birthYear"
                  type="number"
                  placeholder="YYYY"
                  min="1900"
                  max={new Date().getFullYear()}
                  value={formData.birthYear}
                  onChange={(e) => setFormData({...formData, birthYear: e.target.value})}
                  className="bg-gray-700 border-gray-600 text-white placeholder-gray-400 focus:border-purple-500"
                  required
                />
                <p className="text-xs text-gray-400">You must be 18 or older to use this service</p>
              </div>

              <div className="flex items-start">
                <input
                  id="agree-terms"
                  name="agree-terms"
                  type="checkbox"
                  checked={formData.agreeTerms}
                  onChange={(e) => setFormData({...formData, agreeTerms: e.target.checked})}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-600 rounded bg-gray-700 mt-0.5"
                  required
                />
                <label htmlFor="agree-terms" className="ml-2 block text-sm text-gray-300">
                  I agree to the{' '}
                  <Link href="/terms" className="text-purple-400 hover:text-purple-300">
                    Terms of Service
                  </Link>
                  {' '}and{' '}
                  <Link href="/privacy" className="text-purple-400 hover:text-purple-300">
                    Privacy Policy
                  </Link>
                </label>
              </div>

              <Button
                type="submit"
                className="w-full bg-purple-600 hover:bg-purple-700 text-white"
                disabled={isLoading || !isPasswordValid}
              >
                {isLoading ? 'Creating Account...' : 'Create Account'}
              </Button>
            </form>

            <div className="text-center">
              <span className="text-sm text-gray-400">
                Already have an account?{' '}
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