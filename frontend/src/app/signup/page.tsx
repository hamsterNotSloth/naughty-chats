'use client';

import { useState } from 'react';
import { useRouter } from 'next/navigation';
import Link from 'next/link';
import { Layout } from '@/components/layout/Layout';
import { useAuth } from '@/components/providers/AuthProvider';
import { EyeIcon, EyeSlashIcon, CheckIcon, XMarkIcon } from '@heroicons/react/24/outline';

interface PasswordRequirement {
  text: string;
  test: (password: string) => boolean;
}

const passwordRequirements: PasswordRequirement[] = [
  { text: 'At least 8 characters', test: (p) => p.length >= 8 },
  { text: 'Contains uppercase letter', test: (p) => /[A-Z]/.test(p) },
  { text: 'Contains lowercase letter', test: (p) => /[a-z]/.test(p) },
  { text: 'Contains number', test: (p) => /\d/.test(p) },
];

export default function SignUpPage() {
  const router = useRouter();
  const { signUp } = useAuth();
  const [formData, setFormData] = useState({
    email: '',
    username: '',
    password: '',
    birthYear: '',
    agreeTerms: false,
  });
  const [showPassword, setShowPassword] = useState(false);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');
  const [usernameChecking, setUsernameChecking] = useState(false);
  const [usernameAvailable, setUsernameAvailable] = useState<boolean | null>(null);

  const currentYear = new Date().getFullYear();
  const age = formData.birthYear ? currentYear - parseInt(formData.birthYear) : 0;

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    setIsLoading(true);
    setError('');

    // Validate age
    if (age < 18) {
      setError('You must be 18 or older to register');
      setIsLoading(false);
      return;
    }

    // Validate password requirements
    const failedRequirements = passwordRequirements.filter(req => !req.test(formData.password));
    if (failedRequirements.length > 0) {
      setError('Password does not meet all requirements');
      setIsLoading(false);
      return;
    }

    // Validate terms agreement
    if (!formData.agreeTerms) {
      setError('You must agree to the terms and conditions');
      setIsLoading(false);
      return;
    }

    try {
      await signUp(
        formData.email,
        formData.username,
        formData.password,
        parseInt(formData.birthYear),
        formData.agreeTerms
      );
      router.push('/'); // Redirect to home page after successful sign up
    } catch (err) {
      setError(err instanceof Error ? err.message : 'Registration failed');
    } finally {
      setIsLoading(false);
    }
  };

  const handleChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    const { name, value, type, checked } = e.target;
    setFormData(prev => ({
      ...prev,
      [name]: type === 'checkbox' ? checked : value
    }));

    // Clear error when user starts typing
    if (error) setError('');

    // Check username availability with debounce
    if (name === 'username' && value.length >= 3) {
      setUsernameChecking(true);
      setUsernameAvailable(null);
      
      // Simple mock username check (in real app, this would be debounced API call)
      setTimeout(() => {
        const unavailableUsernames = ['admin', 'root', 'user', 'test'];
        setUsernameAvailable(!unavailableUsernames.includes(value.toLowerCase()));
        setUsernameChecking(false);
      }, 500);
    } else if (name === 'username') {
      setUsernameAvailable(null);
      setUsernameChecking(false);
    }
  };

  return (
    <Layout>
      <div className="min-h-[calc(100vh-4rem)] flex">
        {/* Left side - Artwork */}
        <div className="hidden lg:block relative w-0 flex-1">
          <div className="absolute inset-0 h-full w-full bg-gradient-to-br from-indigo-600 to-purple-600 flex items-center justify-center">
            <div className="text-center text-white">
              <h3 className="text-3xl font-bold mb-4">Start Your Journey</h3>
              <p className="text-lg opacity-90 max-w-md">
                Create amazing stories with AI characters. Get 100 free gems to start your adventure!
              </p>
              <div className="mt-8 space-y-4">
                <div className="flex items-center text-left">
                  <CheckIcon className="h-6 w-6 mr-3 text-green-300" />
                  <span>100 Free Gems Welcome Bonus</span>
                </div>
                <div className="flex items-center text-left">
                  <CheckIcon className="h-6 w-6 mr-3 text-green-300" />
                  <span>Access to Thousands of Characters</span>
                </div>
                <div className="flex items-center text-left">
                  <CheckIcon className="h-6 w-6 mr-3 text-green-300" />
                  <span>Create Your Own Characters</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* Right side - Form */}
        <div className="flex-1 flex items-center justify-center px-4 sm:px-6 lg:px-8">
          <div className="max-w-md w-full space-y-8">
            <div>
              <h2 className="mt-6 text-center text-3xl font-extrabold text-gray-900">
                Create your account
              </h2>
              <p className="mt-2 text-center text-sm text-gray-600">
                Already have an account?{' '}
                <Link
                  href="/signin"
                  className="font-medium text-purple-600 hover:text-purple-500"
                >
                  Sign in
                </Link>
              </p>
            </div>
            
            <form className="mt-8 space-y-6" onSubmit={handleSubmit}>
              {error && (
                <div className="bg-red-50 border border-red-300 text-red-700 px-4 py-3 rounded-md" role="alert">
                  {error}
                </div>
              )}

              <div className="space-y-4">
                <div>
                  <label htmlFor="email" className="block text-sm font-medium text-gray-700">
                    Email address
                  </label>
                  <input
                    id="email"
                    name="email"
                    type="email"
                    autoComplete="email"
                    required
                    value={formData.email}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                    placeholder="Enter your email"
                  />
                </div>

                <div>
                  <label htmlFor="username" className="block text-sm font-medium text-gray-700">
                    Username
                  </label>
                  <div className="mt-1 relative">
                    <input
                      id="username"
                      name="username"
                      type="text"
                      autoComplete="username"
                      required
                      value={formData.username}
                      onChange={handleChange}
                      className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                      placeholder="Choose a username"
                    />
                    {formData.username.length >= 3 && (
                      <div className="absolute inset-y-0 right-0 pr-3 flex items-center">
                        {usernameChecking ? (
                          <div className="animate-spin h-4 w-4 border-2 border-purple-500 border-t-transparent rounded-full"></div>
                        ) : usernameAvailable === true ? (
                          <CheckIcon className="h-5 w-5 text-green-500" />
                        ) : usernameAvailable === false ? (
                          <XMarkIcon className="h-5 w-5 text-red-500" />
                        ) : null}
                      </div>
                    )}
                  </div>
                  {usernameAvailable === false && (
                    <p className="mt-1 text-sm text-red-600">Username is not available</p>
                  )}
                  {usernameAvailable === true && (
                    <p className="mt-1 text-sm text-green-600">Username is available</p>
                  )}
                </div>

                <div>
                  <label htmlFor="password" className="block text-sm font-medium text-gray-700">
                    Password
                  </label>
                  <div className="mt-1 relative">
                    <input
                      id="password"
                      name="password"
                      type={showPassword ? 'text' : 'password'}
                      autoComplete="new-password"
                      required
                      value={formData.password}
                      onChange={handleChange}
                      className="block w-full px-3 py-2 pr-10 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                      placeholder="Create a strong password"
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
                    <div className="mt-2 space-y-1">
                      {passwordRequirements.map((requirement, index) => {
                        const isValid = requirement.test(formData.password);
                        return (
                          <div key={index} className={`flex items-center text-sm ${isValid ? 'text-green-600' : 'text-gray-500'}`}>
                            {isValid ? (
                              <CheckIcon className="h-4 w-4 mr-1" />
                            ) : (
                              <XMarkIcon className="h-4 w-4 mr-1" />
                            )}
                            {requirement.text}
                          </div>
                        );
                      })}
                    </div>
                  )}
                </div>

                <div>
                  <label htmlFor="birthYear" className="block text-sm font-medium text-gray-700">
                    Birth Year
                  </label>
                  <input
                    id="birthYear"
                    name="birthYear"
                    type="number"
                    min="1900"
                    max={currentYear}
                    required
                    value={formData.birthYear}
                    onChange={handleChange}
                    className="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm placeholder-gray-400 focus:outline-none focus:ring-purple-500 focus:border-purple-500"
                    placeholder="YYYY"
                  />
                  {formData.birthYear && age < 18 && (
                    <p className="mt-1 text-sm text-red-600">You must be 18 or older to register</p>
                  )}
                  {formData.birthYear && age >= 18 && (
                    <p className="mt-1 text-sm text-green-600">Age verification passed</p>
                  )}
                </div>
              </div>

              <div className="flex items-start">
                <input
                  id="agreeTerms"
                  name="agreeTerms"
                  type="checkbox"
                  checked={formData.agreeTerms}
                  onChange={handleChange}
                  className="h-4 w-4 text-purple-600 focus:ring-purple-500 border-gray-300 rounded mt-1"
                />
                <label htmlFor="agreeTerms" className="ml-2 block text-sm text-gray-900">
                  I agree to the{' '}
                  <Link href="/terms" className="text-purple-600 hover:text-purple-500">
                    Terms of Service
                  </Link>{' '}
                  and{' '}
                  <Link href="/privacy" className="text-purple-600 hover:text-purple-500">
                    Privacy Policy
                  </Link>
                </label>
              </div>

              <div>
                <button
                  type="submit"
                  disabled={isLoading || !formData.agreeTerms || age < 18}
                  className="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md text-white bg-purple-600 hover:bg-purple-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-purple-500 disabled:opacity-50 disabled:cursor-not-allowed"
                >
                  {isLoading ? 'Creating account...' : 'Create account'}
                </button>
              </div>

              {/* Social Login Placeholder */}
              <div className="mt-6">
                <div className="relative">
                  <div className="absolute inset-0 flex items-center">
                    <div className="w-full border-t border-gray-300" />
                  </div>
                  <div className="relative flex justify-center text-sm">
                    <span className="px-2 bg-white text-gray-500">Or continue with</span>
                  </div>
                </div>

                <div className="mt-6 grid grid-cols-2 gap-3">
                  <button
                    type="button"
                    className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                    disabled
                  >
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path d="M6.29 18.251c7.547 0 11.675-6.253 11.675-11.675 0-.178 0-.355-.012-.53A8.348 8.348 0 0020 3.92a8.19 8.19 0 01-2.357.646 4.118 4.118 0 001.804-2.27 8.224 8.224 0 01-2.605.996 4.107 4.107 0 00-6.993 3.743 11.65 11.65 0 01-8.457-4.287 4.106 4.106 0 001.27 5.477A4.073 4.073 0 01.8 7.713v.052a4.105 4.105 0 003.292 4.022 4.095 4.095 0 01-1.853.07 4.108 4.108 0 003.834 2.85A8.233 8.233 0 010 16.407a11.616 11.616 0 006.29 1.84" />
                    </svg>
                    <span className="ml-2">Twitter</span>
                  </button>

                  <button
                    type="button"
                    className="w-full inline-flex justify-center py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50"
                    disabled
                  >
                    <svg className="h-5 w-5" fill="currentColor" viewBox="0 0 20 20">
                      <path fillRule="evenodd" d="M10 0C4.477 0 0 4.484 0 10.017c0 4.425 2.865 8.18 6.839 9.504.5.092.682-.217.682-.483 0-.237-.008-.868-.013-1.703-2.782.605-3.369-1.343-3.369-1.343-.454-1.158-1.11-1.466-1.11-1.466-.908-.62.069-.608.069-.608 1.003.07 1.531 1.032 1.531 1.032.892 1.53 2.341 1.088 2.91.832.092-.647.35-1.088.636-1.338-2.22-.253-4.555-1.113-4.555-4.951 0-1.093.39-1.988 1.029-2.688-.103-.253-.446-1.272.098-2.65 0 0 .84-.27 2.75 1.026A9.564 9.564 0 0110 4.844c.85.004 1.705.115 2.504.337 1.909-1.296 2.747-1.027 2.747-1.027.546 1.379.203 2.398.1 2.651.64.7 1.028 1.595 1.028 2.688 0 3.848-2.339 4.695-4.566 4.942.359.31.678.921.678 1.856 0 1.338-.012 2.419-.012 2.747 0 .268.18.58.688.482A10.019 10.019 0 0020 10.017C20 4.484 15.522 0 10 0z" clipRule="evenodd" />
                    </svg>
                    <span className="ml-2">GitHub</span>
                  </button>
                </div>
                <p className="mt-2 text-xs text-gray-500 text-center">
                  Social login coming soon
                </p>
              </div>
            </form>
          </div>
        </div>
      </div>
    </Layout>
  );
}