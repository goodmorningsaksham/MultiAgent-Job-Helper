'use client';

import { useStore } from '@/stores/useStore';
import { Building2, Plus, Loader2, Trash2 } from 'lucide-react';

interface SidebarProps {
  onNewCompany: () => void;
}

export default function Sidebar({ onNewCompany }: SidebarProps) {
  const { companies, selectedCompany, selectCompany, loadingCompanies, deleteCompany } = useStore();

  return (
    <aside className="w-72 h-screen bg-dark-900/80 border-r border-dark-700/50 flex flex-col">
      <div className="p-4 border-b border-dark-700/50">
        <div className="flex items-center gap-3 mb-4">
          <div className="w-9 h-9 rounded-xl bg-primary-600 flex items-center justify-center">
            <span className="text-white font-bold text-sm">RA</span>
          </div>
          <div>
            <h1 className="text-sm font-semibold text-dark-100">RecruitAI</h1>
            <p className="text-xs text-dark-400">Intelligence Platform</p>
          </div>
        </div>
        <button
          onClick={onNewCompany}
          className="w-full btn-primary flex items-center justify-center gap-2 text-sm"
        >
          <Plus className="w-4 h-4" />
          New Company
        </button>
      </div>

      <div className="flex-1 overflow-y-auto scrollbar-thin p-2">
        {loadingCompanies ? (
          <div className="flex items-center justify-center py-8">
            <Loader2 className="w-5 h-5 text-dark-400 animate-spin" />
          </div>
        ) : companies.length === 0 ? (
          <div className="text-center py-8 px-4">
            <p className="text-dark-400 text-sm">No companies yet</p>
            <p className="text-dark-500 text-xs mt-1">Search for a company to get started</p>
          </div>
        ) : (
          <div className="space-y-1">
            {companies.map((company) => (
              <div
                key={company.id}
                onClick={() => selectCompany(company)}
                className={`w-full text-left px-3 py-2.5 rounded-xl transition-all duration-150 group cursor-pointer flex items-center justify-between ${
                  selectedCompany?.id === company.id
                    ? 'bg-primary-600/10 border border-primary-500/20'
                    : 'hover:bg-dark-800/50'
                }`}
              >
                <div className="flex items-center gap-3 overflow-hidden flex-1">
                  <div className={`w-8 h-8 rounded-lg flex items-center justify-center flex-shrink-0 ${
                    selectedCompany?.id === company.id ? 'bg-primary-600/20' : 'bg-dark-700/50'
                  }`}>
                    <Building2 className={`w-4 h-4 ${
                      selectedCompany?.id === company.id ? 'text-primary-400' : 'text-dark-400'
                    }`} />
                  </div>
                  <div className="flex-1 min-w-0">
                    <p className={`text-sm font-medium truncate ${
                      selectedCompany?.id === company.id ? 'text-primary-300' : 'text-dark-200'
                    }`}>
                      {company.name}
                    </p>
                    <p className="text-xs text-dark-500 truncate">
                      {company.industry || company.domain || 'No industry'}
                    </p>
                  </div>
                  <StatusDot status={company.research_status} />
                </div>
                
                <button
                  onClick={(e) => {
                    e.stopPropagation();
                    if (confirm(`Are you sure you want to delete ${company.name}?`)) {
                      deleteCompany(company.id);
                    }
                  }}
                  className="ml-2 p-1.5 text-dark-500 hover:text-red-400 hover:bg-red-400/10 rounded-lg opacity-0 group-hover:opacity-100 transition-opacity"
                  title="Delete company"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        )}
      </div>
    </aside>
  );
}

function StatusDot({ status }: { status: string }) {
  const colors = {
    completed: 'bg-emerald-400',
    in_progress: 'bg-amber-400 animate-pulse',
    failed: 'bg-red-400',
    pending: 'bg-dark-500',
  };
  return (
    <div className={`w-2 h-2 rounded-full ${colors[status as keyof typeof colors] || colors.pending}`} />
  );
}
