'use client';

import { useEffect, useState } from 'react';
import { useStore } from '@/stores/useStore';
import Sidebar from '@/components/Sidebar';
import CompanyDashboard from '@/components/CompanyDashboard';
import SearchModal from '@/components/SearchModal';
import ErrorBoundary from '@/components/ErrorBoundary';
import ToastContainer from '@/components/Toast';
import { useHotkey } from '@/lib/useHotkey';
import { Menu } from 'lucide-react';

export default function Home() {
  const { fetchCompanies, selectedCompany, error, clearError } = useStore();
  const [showSearch, setShowSearch] = useState(false);
  const [sidebarOpen, setSidebarOpen] = useState(false);

  useHotkey({ key: 'k', ctrl: true, callback: () => setShowSearch(true) });

  useEffect(() => {
    fetchCompanies();
  }, [fetchCompanies]);

  return (
    <ErrorBoundary>
      <div className="flex h-screen overflow-hidden">
        {/* Mobile sidebar overlay */}
        {sidebarOpen && (
          <div
            className="fixed inset-0 bg-dark-950/80 z-40 lg:hidden"
            onClick={() => setSidebarOpen(false)}
          />
        )}

        {/* Sidebar - hidden on mobile, always visible on desktop */}
        <div className={`fixed inset-y-0 left-0 z-50 lg:relative lg:z-0 transform transition-transform duration-300 ease-in-out ${
          sidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        }`}>
          <Sidebar onNewCompany={() => { setShowSearch(true); setSidebarOpen(false); }} />
        </div>

        <main className="flex-1 overflow-y-auto scrollbar-thin">
          {/* Mobile header */}
          <div className="lg:hidden flex items-center gap-3 px-4 py-3 border-b border-dark-700/50">
            <button
              onClick={() => setSidebarOpen(true)}
              className="btn-ghost p-2"
              aria-label="Open sidebar"
            >
              <Menu className="w-5 h-5" />
            </button>
            <span className="text-sm font-medium text-dark-200">RecruitAI</span>
          </div>

          {selectedCompany ? (
            <CompanyDashboard />
          ) : (
            <div className="flex items-center justify-center h-full px-4">
              <div className="text-center max-w-md">
                <div className="w-20 h-20 mx-auto mb-6 rounded-2xl bg-primary-600/10 flex items-center justify-center">
                  <svg className="w-10 h-10 text-primary-400" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={1.5} d="M21 21l-5.197-5.197m0 0A7.5 7.5 0 105.196 5.196a7.5 7.5 0 0010.607 10.607z" />
                  </svg>
                </div>
                <h2 className="text-2xl font-semibold text-dark-100 mb-2">Start Your Research</h2>
                <p className="text-dark-400 mb-6">
                  Search for a company to begin AI-powered recruiting intelligence gathering.
                </p>
                <button
                  onClick={() => setShowSearch(true)}
                  className="btn-primary"
                  aria-label="Search for a company"
                >
                  Search Company
                </button>
                <div className="mt-8 grid grid-cols-3 gap-4 text-center">
                  <div className="glass-card p-3">
                    <p className="text-2xl font-bold text-primary-400">5</p>
                    <p className="text-[10px] text-dark-400 uppercase">AI Agents</p>
                  </div>
                  <div className="glass-card p-3">
                    <p className="text-2xl font-bold text-emerald-400">RAG</p>
                    <p className="text-[10px] text-dark-400 uppercase">Powered Chat</p>
                  </div>
                  <div className="glass-card p-3">
                    <p className="text-2xl font-bold text-amber-400">AI</p>
                    <p className="text-[10px] text-dark-400 uppercase">Eval Layer</p>
                  </div>
                </div>
              </div>
            </div>
          )}
        </main>

        {showSearch && <SearchModal onClose={() => setShowSearch(false)} />}

        {error && (
          <div className="fixed bottom-4 right-4 z-50 bg-red-500/10 border border-red-500/30 rounded-xl px-4 py-3 flex items-center gap-3 max-w-sm shadow-lg">
            <span className="text-red-400 text-sm">{error}</span>
            <button onClick={clearError} className="text-red-400 hover:text-red-300 text-lg leading-none" aria-label="Dismiss error">&times;</button>
          </div>
        )}

        <ToastContainer />
      </div>
    </ErrorBoundary>
  );
}
