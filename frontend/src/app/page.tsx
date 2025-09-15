'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Layout } from '@/components/layout/Layout';
import { CharacterCard } from '@/components/characters/CharacterCard';
import { useAuth } from '@/components/providers/AuthProvider';

interface Character {
  id: number;
  name: string;
  avatarUrl: string;
  shortDescription: string;
  tags: string[];
  ratingAvg: number;
  ratingCount: number;
  gemCostPerMessage?: number;
  nsfwFlags: boolean;
  lastActive: string;
}

interface CharacterListResponse {
  items: Character[];
  nextCursor?: string;
}

export default function HomePage() {
  const { user } = useAuth();
  const [activeTab, setActiveTab] = useState<'fast_load' | 'popular' | 'new'>('popular');

  const { data, isLoading, error, refetch, isError } = useQuery<CharacterListResponse>({
    queryKey: ['characters', activeTab],
    queryFn: async () => {
      const base = process.env.NEXT_PUBLIC_API_BASE_URL || 'http://localhost:8000';
      const response = await fetch(`${base}/api/characters?sort=${activeTab}&limit=12`);
      if (!response.ok) {
        let detail = 'Failed to fetch characters';
        try {
          const errBody = await response.json();
          if (errBody?.detail) detail = errBody.detail;
        } catch (_) {}
        throw new Error(detail);
      }
      return response.json();
    },
  });

  const tabs = [
    { id: 'fast_load' as const, name: 'Fast Load', description: 'Quick to start' },
    { id: 'popular' as const, name: 'Popular', description: 'Highly rated' },
    { id: 'new' as const, name: 'New', description: 'Recently added' },
  ];

  return (
    <Layout>
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Hero Section */}
        <div className="text-center mb-12">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">
            Discover Amazing AI Characters
          </h1>
          <p className="text-xl text-gray-600 mb-8">
            Chat with unique personalities, explore different scenarios, and create unforgettable experiences
          </p>
          
          {/* Welcome Bonus Banner */}
          {!user && (
            <div className="bg-gradient-to-r from-purple-600 to-pink-600 text-white rounded-lg p-6 mb-8">
              <h2 className="text-2xl font-bold mb-2">Get Started with 100 Free Gems!</h2>
              <p className="mb-4">Sign up now and start chatting with AI characters immediately</p>
              <div className="space-x-4">
                <a
                  href="/signup"
                  className="bg-white text-purple-600 px-6 py-3 rounded-lg font-semibold hover:bg-gray-100 transition-colors"
                >
                  Sign Up Free
                </a>
                <a
                  href="https://discord.gg/naughty-chats"
                  target="_blank"
                  rel="noopener noreferrer"
                  className="border-2 border-white text-white px-6 py-3 rounded-lg font-semibold hover:bg-white hover:text-purple-600 transition-colors"
                >
                  Join Discord
                </a>
              </div>
            </div>
          )}
        </div>

        {/* Tab Navigation */}
        <div className="flex justify-center mb-8">
          <div className="bg-white rounded-lg p-1 shadow-sm border">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                onClick={() => setActiveTab(tab.id)}
                className={`px-6 py-2 rounded-md font-medium transition-colors ${
                  activeTab === tab.id
                    ? 'bg-purple-600 text-white'
                    : 'text-gray-600 hover:text-gray-900 hover:bg-gray-50'
                }`}
              >
                {tab.name}
              </button>
            ))}
          </div>
        </div>

        {/* Character Grid */}
        <div className="mb-8">
          {isLoading && (
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
              {[...Array(8)].map((_, i) => (
                <div key={i} className="bg-white rounded-lg shadow-md overflow-hidden animate-pulse">
                  <div className="h-48 bg-gray-300"></div>
                  <div className="p-4 space-y-2">
                    <div className="h-4 bg-gray-300 rounded w-3/4"></div>
                    <div className="h-3 bg-gray-300 rounded w-full"></div>
                    <div className="h-3 bg-gray-300 rounded w-2/3"></div>
                  </div>
                </div>
              ))}
            </div>
          )}

          {isError && error && (
            <div className="text-center py-12">
              <p className="text-red-600 mb-4">{error.message}</p>
              <button
                onClick={() => refetch()}
                className="bg-purple-600 text-white px-4 py-2 rounded-lg hover:bg-purple-700 transition-colors"
              >
                Retry
              </button>
            </div>
          )}

          {data && (
            <>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
                {data.items.map((character) => (
                  <CharacterCard key={character.id} {...character} />
                ))}
              </div>

              {data.items.length === 0 && (
                <div className="text-center py-12">
                  <p className="text-gray-600 mb-4">No characters found in this category.</p>
                  <p className="text-gray-500">Try switching to a different tab or check back later.</p>
                </div>
              )}
            </>
          )}
        </div>

        {/* Discord CTA Section */}
        <div className="bg-indigo-50 rounded-lg p-8 text-center">
          <h2 className="text-2xl font-bold text-gray-900 mb-4">
            Join Our Community
          </h2>
          <p className="text-gray-600 mb-6">
            Connect with other users, get updates, and share your favorite characters on Discord
          </p>
          <a
            href="https://discord.gg/naughty-chats"
            target="_blank"
            rel="noopener noreferrer"
            className="bg-indigo-600 text-white px-8 py-3 rounded-lg font-semibold hover:bg-indigo-700 transition-colors inline-flex items-center"
          >
            <svg className="w-5 h-5 mr-2" fill="currentColor" viewBox="0 0 20 20">
              <path d="M16.707 5.293a1 1 0 010 1.414l-8 8a1 1 0 01-1.414 0l-4-4a1 1 0 011.414-1.414L8 12.586l7.293-7.293a1 1 0 011.414 0z" />
            </svg>
            Join Discord Community
          </a>
        </div>
      </div>
    </Layout>
  );
}
