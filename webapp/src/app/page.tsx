'use client'

import { useState } from 'react'
import Link from 'next/link'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card'

// Mock character data based on the specifications
const mockCharacters = [
  {
    id: 1,
    name: "Elena",
    avatarUrl: "/api/placeholder/300/400",
    shortDescription: "Mysterious librarian with ancient secrets",
    tags: ["fantasy", "mystery", "intellectual"],
    ratingAvg: 4.8,
    ratingCount: 156,
    gemCostPerMessage: 2,
    nsfwFlags: false
  },
  {
    id: 2,
    name: "Alex",
    avatarUrl: "/api/placeholder/300/400",
    shortDescription: "Cyberpunk hacker from 2087",
    tags: ["sci-fi", "cyberpunk", "tech"],
    ratingAvg: 4.6,
    ratingCount: 89,
    gemCostPerMessage: 3,
    nsfwFlags: false
  },
  {
    id: 3,
    name: "Luna",
    avatarUrl: "/api/placeholder/300/400",
    shortDescription: "Celestial guardian of dreams",
    tags: ["fantasy", "supernatural", "guardian"],
    ratingAvg: 4.9,
    ratingCount: 203,
    gemCostPerMessage: 4,
    nsfwFlags: false
  },
  {
    id: 4,
    name: "Kai",
    avatarUrl: "/api/placeholder/300/400",
    shortDescription: "Modern-day vampire with a heart",
    tags: ["vampire", "romance", "modern"],
    ratingAvg: 4.7,
    ratingCount: 124,
    gemCostPerMessage: 3,
    nsfwFlags: false
  }
]

function CharacterCard({ character }: { character: typeof mockCharacters[0] }) {
  return (
    <Card className="group cursor-pointer transition-all duration-200 hover:scale-105 hover:shadow-xl bg-gray-800 border-gray-700 hover:border-purple-500">
      <CardHeader className="p-0">
        <div className="aspect-[3/4] overflow-hidden rounded-t-lg">
          <div className="w-full h-full bg-gradient-to-br from-purple-400 to-pink-400 flex items-center justify-center">
            <span className="text-2xl font-bold text-white">{character.name[0]}</span>
          </div>
        </div>
      </CardHeader>
      <CardContent className="p-4">
        <CardTitle className="text-lg text-white group-hover:text-purple-300 transition-colors">
          {character.name}
        </CardTitle>
        <CardDescription className="text-gray-400 mt-1 text-sm line-clamp-2">
          {character.shortDescription}
        </CardDescription>
        <div className="flex flex-wrap gap-1 mt-2">
          {character.tags.slice(0, 2).map((tag) => (
            <span
              key={tag}
              className="px-2 py-1 text-xs bg-gray-700 text-gray-300 rounded-full"
            >
              {tag}
            </span>
          ))}
        </div>
        <div className="flex items-center justify-between mt-3">
          <div className="flex items-center space-x-1">
            <span className="text-yellow-400">★</span>
            <span className="text-sm text-gray-300">{character.ratingAvg}</span>
            <span className="text-xs text-gray-500">({character.ratingCount})</span>
          </div>
          <div className="text-sm text-purple-400">
            {character.gemCostPerMessage} gems/msg
          </div>
        </div>
      </CardContent>
    </Card>
  )
}

export default function HomePage() {
  const [activeTab, setActiveTab] = useState('Fast Load')
  const tabs = ['Fast Load', 'Popular', 'New']

  return (
    <div className="min-h-screen bg-gray-900">
      {/* Hero Banner */}
      <div className="bg-gradient-to-r from-purple-900 via-purple-800 to-pink-800 py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h1 className="text-4xl md:text-6xl font-bold text-white mb-4">
            Welcome to NaughtyChats
          </h1>
          <p className="text-xl text-purple-100 mb-8 max-w-3xl mx-auto">
            Discover immersive AI characters and engage in limitless roleplay experiences. 
            Create your own characters or explore thousands created by our community.
          </p>
          <div className="flex flex-col sm:flex-row gap-4 justify-center">
            <Link href="/signup">
              <Button size="lg" className="bg-white text-purple-900 hover:bg-purple-100 font-semibold">
                Start Free - Get 100 Gems
              </Button>
            </Link>
            <Link href="/discord">
              <Button size="lg" variant="outline" className="border-white text-white hover:bg-white hover:text-purple-900">
                Join Discord Community
              </Button>
            </Link>
          </div>
        </div>
      </div>

      {/* Character Discovery Section */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Category Tabs */}
        <div className="flex flex-col sm:flex-row sm:items-center justify-between mb-8">
          <h2 className="text-3xl font-bold text-white mb-4 sm:mb-0">
            Discover Characters
          </h2>
          <div className="flex space-x-1 bg-gray-800 rounded-lg p-1">
            {tabs.map((tab) => (
              <button
                key={tab}
                onClick={() => setActiveTab(tab)}
                className={`px-4 py-2 rounded-md text-sm font-medium transition-all ${
                  activeTab === tab
                    ? 'bg-purple-600 text-white shadow-md'
                    : 'text-gray-400 hover:text-white hover:bg-gray-700'
                }`}
              >
                {tab}
              </button>
            ))}
          </div>
        </div>

        {/* Character Grid */}
        <div className="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-4 gap-6">
          {mockCharacters.map((character) => (
            <CharacterCard key={character.id} character={character} />
          ))}
        </div>

        {/* Load More */}
        <div className="text-center mt-12">
          <Button variant="outline" size="lg" className="border-purple-500 text-purple-400 hover:bg-purple-500 hover:text-white">
            Load More Characters
          </Button>
        </div>
      </div>

      {/* Discord CTA Section */}
      <div className="bg-gradient-to-r from-blue-900 to-purple-900 py-16">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 text-center">
          <h3 className="text-3xl font-bold text-white mb-4">
            Join Our Growing Community
          </h3>
          <p className="text-xl text-blue-100 mb-8">
            Connect with thousands of creators, share your characters, and get exclusive updates
          </p>
          <Link href="/discord">
            <Button size="lg" className="bg-blue-600 hover:bg-blue-700 text-white font-semibold">
              Join Discord Server
            </Button>
          </Link>
        </div>
      </div>
    </div>
  )
}
