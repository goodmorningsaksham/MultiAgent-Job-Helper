import type { Metadata } from 'next'
import './globals.css'

export const metadata: Metadata = {
  title: 'RecruitAI - Intelligent Recruiting Agent',
  description: 'AI-powered company research and recruiting intelligence platform',
}

export default function RootLayout({
  children,
}: {
  children: React.ReactNode
}) {
  return (
    <html lang="en" className="dark">
      <body className="bg-dark-950 text-dark-100 min-h-screen antialiased">
        {children}
      </body>
    </html>
  )
}
