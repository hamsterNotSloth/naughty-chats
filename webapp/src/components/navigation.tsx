'use client'

import Link from 'next/link'
import { useState } from 'react'
import { Button } from '@/components/ui/button'
import { Bars3Icon, XMarkIcon } from '@heroicons/react/24/outline'

export default function Navigation() {
  const [isMenuOpen, setIsMenuOpen] = useState(false)
  
  return (
    <nav className="bg-gray-900 border-b border-gray-800">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex justify-between h-16">
          <div className="flex items-center">
            <Link href="/" className="text-2xl font-bold text-purple-400">
              NaughtyChats
            </Link>
          </div>
          
          {/* Desktop Navigation */}
          <div className="hidden md:flex items-center space-x-6">
            <Link href="/" className="text-gray-300 hover:text-white transition-colors">
              Explore
            </Link>
            <Link href="/roleplay" className="text-gray-300 hover:text-white transition-colors">
              Roleplay
            </Link>
            <Link href="/tavern" className="text-gray-300 hover:text-white transition-colors">
              Tavern
            </Link>
            <Link href="/generate" className="text-gray-300 hover:text-white transition-colors">
              Generate
            </Link>
            <Link href="/affiliate" className="text-gray-300 hover:text-white transition-colors">
              Affiliate
            </Link>
            <Button variant="outline" className="text-yellow-400 border-yellow-400 hover:bg-yellow-400 hover:text-black">
              Get Gems
            </Button>
            <Link href="/discord" className="text-blue-400 hover:text-blue-300 transition-colors">
              Join Discord
            </Link>
            <div className="flex items-center space-x-3">
              <Link href="/signin">
                <Button variant="ghost" className="text-gray-300 hover:text-white">
                  Sign In
                </Button>
              </Link>
              <Link href="/signup">
                <Button className="bg-purple-600 hover:bg-purple-700">
                  Sign Up
                </Button>
              </Link>
            </div>
          </div>
          
          {/* Mobile menu button */}
          <div className="md:hidden flex items-center">
            <button
              onClick={() => setIsMenuOpen(!isMenuOpen)}
              className="text-gray-300 hover:text-white"
            >
              {isMenuOpen ? (
                <XMarkIcon className="h-6 w-6" />
              ) : (
                <Bars3Icon className="h-6 w-6" />
              )}
            </button>
          </div>
        </div>
      </div>
      
      {/* Mobile Navigation */}
      {isMenuOpen && (
        <div className="md:hidden">
          <div className="px-2 pt-2 pb-3 space-y-1 sm:px-3 bg-gray-800">
            <Link href="/" className="block px-3 py-2 text-gray-300 hover:text-white">
              Explore
            </Link>
            <Link href="/roleplay" className="block px-3 py-2 text-gray-300 hover:text-white">
              Roleplay
            </Link>
            <Link href="/tavern" className="block px-3 py-2 text-gray-300 hover:text-white">
              Tavern
            </Link>
            <Link href="/generate" className="block px-3 py-2 text-gray-300 hover:text-white">
              Generate
            </Link>
            <Link href="/affiliate" className="block px-3 py-2 text-gray-300 hover:text-white">
              Affiliate
            </Link>
            <Link href="/gems" className="block px-3 py-2 text-yellow-400 hover:text-yellow-300">
              Get Gems
            </Link>
            <Link href="/discord" className="block px-3 py-2 text-blue-400 hover:text-blue-300">
              Join Discord
            </Link>
            <div className="border-t border-gray-600 pt-4 pb-3">
              <div className="flex items-center px-3 space-x-3">
                <Link href="/signin">
                  <Button variant="ghost" className="text-gray-300 hover:text-white">
                    Sign In
                  </Button>
                </Link>
                <Link href="/signup">
                  <Button className="bg-purple-600 hover:bg-purple-700">
                    Sign Up
                  </Button>
                </Link>
              </div>
            </div>
          </div>
        </div>
      )}
    </nav>
  )
}