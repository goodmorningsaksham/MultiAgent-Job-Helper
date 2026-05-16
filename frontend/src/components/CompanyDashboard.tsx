'use client';

import { useEffect, useRef } from 'react';
import { useStore } from '@/stores/useStore';
import { Building2, Users, Mail, MessageSquare, BarChart3, Loader2, CheckCircle2, Clock, RefreshCw } from 'lucide-react';
import OverviewTab from '@/components/tabs/OverviewTab';
import PeopleTab from '@/components/tabs/PeopleTab';
import TemplatesTab from '@/components/tabs/TemplatesTab';
import ChatTab from '@/components/tabs/ChatTab';
import EvaluationTab from '@/components/tabs/EvaluationTab';

const POLL_INTERVAL_MS = 3000;

const TABS = [
  { key: 'overview', label: 'Overview', icon: Building2 },
  { key: 'people', label: 'People', icon: Users },
  { key: 'templates', label: 'Templates', icon: Mail },
  { key: 'chat', label: 'Chat', icon: MessageSquare },
  { key: 'evaluation', label: 'Evaluation', icon: BarChart3 },
] as const;

export default function CompanyDashboard() {
  const {
    selectedCompany,
    activeTab,
    setActiveTab,
    isResearching,
    researchStatus,
    pollResearchStatus,
    startResearch,
  } = useStore();

  const pollingRef = useRef(false);

  // Fallback polling — only activates if SSE fails (store sets isResearching back to true without SSE)
  useEffect(() => {
    if (!isResearching || !selectedCompany) return;
    // Give SSE 5 seconds to connect before falling back to polling
    const fallbackTimer = setTimeout(() => {
      if (!pollingRef.current && isResearching) {
        pollingRef.current = true;
        const interval = setInterval(() => {
          pollResearchStatus(selectedCompany.id);
        }, POLL_INTERVAL_MS);
        return () => {
          clearInterval(interval);
          pollingRef.current = false;
        };
      }
    }, 5000);

    return () => {
      clearTimeout(fallbackTimer);
      pollingRef.current = false;
    };
  }, [isResearching, selectedCompany, pollResearchStatus]);

  if (!selectedCompany) return null;

  return (
    <div className="h-full flex flex-col">
      {/* Header */}
      <header className="px-4 md:px-8 py-5 border-b border-dark-700/50 bg-dark-900/30">
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-4">
            <div className="w-12 h-12 rounded-2xl bg-primary-600/10 flex items-center justify-center">
              <Building2 className="w-6 h-6 text-primary-400" />
            </div>
            <div>
              <h1 className="text-xl font-semibold text-dark-50">{selectedCompany.name}</h1>
              <p className="text-sm text-dark-400">
                {selectedCompany.industry || 'Industry unknown'}
                {selectedCompany.location && ` • ${selectedCompany.location}`}
              </p>
            </div>
          </div>
          <div className="flex items-center gap-3">
            {selectedCompany.research_status === 'completed' && !isResearching && (
              <button
                onClick={() => startResearch(selectedCompany.id)}
                className="btn-ghost text-xs flex items-center gap-1.5"
                aria-label="Re-research company"
              >
                <RefreshCw className="w-3.5 h-3.5" />
                <span className="hidden sm:inline">Re-research</span>
              </button>
            )}
            <ResearchBadge status={selectedCompany.research_status} isActive={isResearching} />
          </div>
        </div>

        {/* Research Progress */}
        {isResearching && researchStatus && (
          <div className="mt-4">
            <ResearchProgress status={researchStatus} />
          </div>
        )}
      </header>

      {/* Tabs */}
      <nav className="px-8 border-b border-dark-700/50 bg-dark-900/20">
        <div className="flex gap-1">
          {TABS.map(({ key, label, icon: Icon }) => (
            <button
              key={key}
              onClick={() => setActiveTab(key)}
              className={`flex items-center gap-2 px-4 py-3 text-sm font-medium border-b-2 transition-all ${
                activeTab === key
                  ? 'border-primary-500 text-primary-400'
                  : 'border-transparent text-dark-400 hover:text-dark-200 hover:border-dark-600'
              }`}
            >
              <Icon className="w-4 h-4" />
              {label}
            </button>
          ))}
        </div>
      </nav>

      {/* Tab Content */}
      <div className="flex-1 overflow-y-auto scrollbar-thin">
        {activeTab === 'overview' && <OverviewTab />}
        {activeTab === 'people' && <PeopleTab />}
        {activeTab === 'templates' && <TemplatesTab />}
        {activeTab === 'chat' && <ChatTab />}
        {activeTab === 'evaluation' && <EvaluationTab />}
      </div>
    </div>
  );
}

function ResearchBadge({ status, isActive }: { status: string; isActive: boolean }) {
  if (isActive) {
    return (
      <div className="badge-warning flex items-center gap-1.5">
        <Loader2 className="w-3 h-3 animate-spin" />
        Researching...
      </div>
    );
  }
  if (status === 'completed') {
    return (
      <div className="badge-success flex items-center gap-1.5">
        <CheckCircle2 className="w-3 h-3" />
        Research Complete
      </div>
    );
  }
  if (status === 'failed') {
    return <div className="badge-error">Research Failed</div>;
  }
  return (
    <div className="badge-info flex items-center gap-1.5">
      <Clock className="w-3 h-3" />
      Pending
    </div>
  );
}

const STEPS = ['research', 'people', 'synthesis', 'evaluation'];

function ResearchProgress({ status }: { status: { completed_steps: string[]; current_step?: string } }) {
  return (
    <div className="flex items-center gap-2">
      {STEPS.map((step, idx) => {
        const isComplete = status.completed_steps.includes(step);
        const isCurrent = status.current_step === step;
        return (
          <div key={step} className="flex items-center gap-2">
            <div className={`flex items-center gap-1.5 px-3 py-1 rounded-full text-xs font-medium ${
              isComplete ? 'bg-emerald-500/10 text-emerald-400' :
              isCurrent ? 'bg-amber-500/10 text-amber-400' :
              'bg-dark-800 text-dark-500'
            }`}>
              {isComplete ? <CheckCircle2 className="w-3 h-3" /> :
               isCurrent ? <Loader2 className="w-3 h-3 animate-spin" /> :
               <Clock className="w-3 h-3" />}
              {step.charAt(0).toUpperCase() + step.slice(1)}
            </div>
            {idx < STEPS.length - 1 && (
              <div className={`w-4 h-px ${isComplete ? 'bg-emerald-500/50' : 'bg-dark-700'}`} />
            )}
          </div>
        );
      })}
    </div>
  );
}
