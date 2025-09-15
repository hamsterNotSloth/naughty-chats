'use client';

import { createContext, useContext, useEffect, useState } from 'react';

interface User {
  id: number;
  email: string;
  username: string;
  gemBalance: number;
  isActive: boolean;
}

interface AuthContextType {
  user: User | null;
  isLoading: boolean;
  signIn: (identifier: string, password: string) => Promise<void>;
  signUp: (email: string, password: string, agreeTerms: boolean) => Promise<void>;
  signOut: () => void;
}

const AuthContext = createContext<AuthContextType | undefined>(undefined);

export function AuthProvider({ children }: { children: React.ReactNode }) {
  const [user, setUser] = useState<User | null>(null);
  const [isLoading, setIsLoading] = useState(true);

  useEffect(() => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const token = localStorage.getItem('access_token');
    if (token) {
      fetch(`${apiBase}/api/me`, {
        headers: { 'Authorization': `Bearer ${token}` },
      })
        .then(response => {
          if (response.ok) {
            return response.json();
          }
          throw new Error('Failed to fetch user');
        })
        .then(userData => {
          setUser(userData);
        })
        .catch(() => {
          localStorage.removeItem('access_token');
        })
        .finally(() => {
          setIsLoading(false);
        });
    } else {
      setIsLoading(false);
    }
  }, []);

  const signIn = async (identifier: string, password: string) => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const response = await fetch(`${apiBase}/api/auth/login`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ identifier, password }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Login failed');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    setUser(data.user);
  };

  const signUp = async (email: string, password: string, agreeTerms: boolean) => {
    const apiBase = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
    const response = await fetch(`${apiBase}/api/auth/register`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
      },
      body: JSON.stringify({ email, password, agreeTerms }),
    });

    if (!response.ok) {
      const error = await response.json();
      throw new Error(error.detail || 'Registration failed');
    }

    const data = await response.json();
    localStorage.setItem('access_token', data.access_token);
    setUser(data.user);
  };

  const signOut = () => {
    localStorage.removeItem('access_token');
    setUser(null);
  };

  return (
    <AuthContext.Provider value={{ user, isLoading, signIn, signUp, signOut }}>
      {children}
    </AuthContext.Provider>
  );
}

export function useAuth() {
  const context = useContext(AuthContext);
  if (context === undefined) {
    throw new Error('useAuth must be used within an AuthProvider');
  }
  return context;
}