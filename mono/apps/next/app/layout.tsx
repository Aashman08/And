import type { Metadata } from 'next'
import { Inter } from 'next/font/google'
import './globals.css'

const inter = Inter({ subsets: ['latin'] })

export const metadata: Metadata = {
  title: 'R&D Discovery System',
  description: 'AI-powered search for research papers and startups',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en">
      <body className={inter.className}>
        <div className="min-h-screen flex flex-col">
          {/* Header */}
          <header className="bg-white border-b border-gray-200">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
              <div className="flex items-center justify-between">
                <div className="flex items-center space-x-3">
                  <div className="w-10 h-10 bg-primary-600 rounded-lg flex items-center justify-center">
                    <span className="text-white font-bold text-xl">R</span>
                  </div>
                  <div>
                    <h1 className="text-xl font-bold text-gray-900">R&D Discovery</h1>
                    <p className="text-sm text-gray-500">Research Papers & Startups</p>
                  </div>
                </div>
                <nav className="flex items-center space-x-6">
                  <a href="/" className="text-gray-700 hover:text-primary-600 font-medium">
                    Search
                  </a>
                  <a href="/about" className="text-gray-500 hover:text-primary-600">
                    About
                  </a>
                </nav>
              </div>
            </div>
          </header>

          {/* Main content */}
          <main className="flex-1">
            {children}
          </main>

          {/* Footer */}
          <footer className="bg-gray-50 border-t border-gray-200 mt-auto">
            <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
              <p className="text-center text-sm text-gray-500">
                © 2025 R&D Discovery System. Powered by hybrid search + AI.
              </p>
            </div>
          </footer>
        </div>
      </body>
    </html>
  )
}

