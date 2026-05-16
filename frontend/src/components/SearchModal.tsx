'use client';

import { useState } from 'react';
import { useStore } from '@/stores/useStore';
import api, { CompanySearchResult } from '@/services/api';
import { Search, X, Loader2, Globe, Building2 } from 'lucide-react';

interface SearchModalProps {
  onClose: () => void;
}

export default function SearchModal({ onClose }: SearchModalProps) {
  const { createCompany, startResearch, selectCompany } = useStore();
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<CompanySearchResult[]>([]);
  const [loading, setLoading] = useState(false);
  const [creating, setCreating] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;
    setLoading(true);
    const res = await api.searchCompanies(query);
    if (res.ok) {
      setResults(res.data!);
    }
    setLoading(false);
  };

  const handleSelect = async (result: CompanySearchResult) => {
    setCreating(true);
    const company = await createCompany(result.name, result.domain, result.website);
    if (company) {
      await startResearch(company.id);
      selectCompany(company);
      onClose();
    }
    setCreating(false);
  };

  const handleCreateCustom = async () => {
    if (!query.trim()) return;
    setCreating(true);
    const company = await createCompany(query);
    if (company) {
      await startResearch(company.id);
      selectCompany(company);
      onClose();
    }
    setCreating(false);
  };

  return (
    <div className="fixed inset-0 z-50 flex items-start justify-center pt-[15vh]">
      <div className="absolute inset-0 bg-dark-950/80 backdrop-blur-sm" onClick={onClose} />

      <div className="relative w-full max-w-2xl glass-card p-0 overflow-hidden shadow-2xl">
        <div className="flex items-center gap-3 px-5 py-4 border-b border-dark-700/50">
          <Search className="w-5 h-5 text-dark-400" />
          <input
            type="text"
            placeholder="Search for a company (e.g., Stripe, Vercel, Anthropic)..."
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && handleSearch()}
            className="flex-1 bg-transparent text-dark-100 placeholder:text-dark-400 focus:outline-none text-lg"
            autoFocus
          />
          {loading ? (
            <Loader2 className="w-5 h-5 text-dark-400 animate-spin" />
          ) : (
            <button onClick={onClose} className="text-dark-400 hover:text-dark-200">
              <X className="w-5 h-5" />
            </button>
          )}
        </div>

        <div className="max-h-[50vh] overflow-y-auto scrollbar-thin">
          {results.length > 0 ? (
            <div className="p-2">
              {results.map((result, idx) => (
                <button
                  key={idx}
                  onClick={() => handleSelect(result)}
                  disabled={creating}
                  className="w-full text-left px-4 py-3 rounded-xl hover:bg-dark-800/50 transition-colors group disabled:opacity-50"
                >
                  <div className="flex items-center gap-3">
                    <div className="w-10 h-10 rounded-xl bg-dark-700/50 flex items-center justify-center group-hover:bg-primary-600/10">
                      <Building2 className="w-5 h-5 text-dark-400 group-hover:text-primary-400" />
                    </div>
                    <div className="flex-1 min-w-0">
                      <p className="text-sm font-medium text-dark-100">{result.name}</p>
                      <p className="text-xs text-dark-400 truncate">
                        {result.description || result.domain || 'Company'}
                      </p>
                    </div>
                    {result.website && (
                      <Globe className="w-4 h-4 text-dark-500" />
                    )}
                  </div>
                </button>
              ))}
            </div>
          ) : query && !loading ? (
            <div className="p-6 text-center">
              <p className="text-dark-400 text-sm mb-3">No results found for &quot;{query}&quot;</p>
              <button
                onClick={handleCreateCustom}
                disabled={creating}
                className="btn-secondary text-sm"
              >
                {creating ? <Loader2 className="w-4 h-4 animate-spin" /> : `Research "${query}" anyway`}
              </button>
            </div>
          ) : (
            <div className="p-6 text-center text-dark-500 text-sm">
              Type a company name and press Enter to search
            </div>
          )}
        </div>

        {results.length > 0 && (
          <div className="px-5 py-3 border-t border-dark-700/50 bg-dark-900/50">
            <button
              onClick={handleCreateCustom}
              disabled={creating}
              className="text-sm text-dark-400 hover:text-primary-400 transition-colors"
            >
              {creating ? 'Creating...' : `Don't see it? Research "${query}" directly`}
            </button>
          </div>
        )}
      </div>
    </div>
  );
}
