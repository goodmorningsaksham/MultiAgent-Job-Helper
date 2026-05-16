'use client';

import { useStore } from '@/stores/useStore';
import { Globe, MapPin, Briefcase, TrendingUp, Code2, Lightbulb, AlertCircle, Loader2, CheckCircle2, Circle } from 'lucide-react';

const PIPELINE_STEPS = [
  { id: 'research', label: 'Company Research' },
  { id: 'people', label: 'People Discovery' },
  { id: 'synthesis', label: 'Data Synthesis' },
  { id: 'evaluation', label: 'Evaluation Phase' },
  { id: 'complete', label: 'Ready' }
];

export default function OverviewTab() {
  const { selectedCompany, researchStatus } = useStore();
  if (!selectedCompany) return null;

  const company = selectedCompany;
  const synthesis = company.meta_data?.synthesis;

  if (!synthesis && (company.research_status !== 'completed' && company.research_status !== 'failed')) {
    const currentStep = researchStatus?.current_step || 'research';
    const completedSteps = researchStatus?.completed_steps || [];

    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="w-full max-w-xl">
          <div className="text-center mb-8">
            <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-primary-600/10 flex items-center justify-center">
              <Loader2 className="w-8 h-8 text-primary-400 animate-spin" />
            </div>
            <h3 className="text-xl font-semibold text-dark-100 mb-2">Research Pipeline Active</h3>
            <p className="text-dark-400">Our multi-agent system is currently gathering intelligence.</p>
          </div>

          <div className="bg-dark-800/50 rounded-2xl p-6 border border-dark-700/50">
            <div className="space-y-2">
              {PIPELINE_STEPS.map((step, idx) => {
                const isCompleted = completedSteps.includes(step.id) || (step.id === 'complete' && company.research_status === 'completed');
                const isCurrent = currentStep === step.id; 
                const isPending = !isCompleted && !isCurrent;

                return (
                  <div key={step.id} className="flex flex-col">
                    <div className="flex items-center gap-4">
                      <div className={`flex-shrink-0 flex items-center justify-center w-8 h-8 rounded-full ${
                        isCompleted ? 'text-emerald-400 bg-emerald-400/10' :
                        isCurrent ? 'text-primary-400 bg-primary-400/10' :
                        'text-dark-500 bg-dark-700/50'
                      }`}>
                        {isCompleted ? <CheckCircle2 className="w-4 h-4" /> : 
                         isCurrent ? <Loader2 className="w-4 h-4 animate-spin" /> : 
                         <Circle className="w-4 h-4" />}
                      </div>
                      <div className="flex-1 py-2">
                        <h4 className={`text-sm font-medium ${
                          isCompleted ? 'text-dark-100' :
                          isCurrent ? 'text-primary-300' :
                          'text-dark-400'
                        }`}>
                          {step.label} {isCurrent && '(Running)'}
                        </h4>
                      </div>
                    </div>
                    {idx < PIPELINE_STEPS.length - 1 && (
                      <div className="ml-4 h-4 border-l-2 border-dark-700/50" />
                    )}
                  </div>
                );
              })}
            </div>
          </div>
        </div>
      </div>
    );
  }

  if (!synthesis && company.research_status === 'failed') {
    return (
      <div className="p-8 flex items-center justify-center h-full">
        <div className="text-center max-w-md">
          <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-red-500/10 flex items-center justify-center">
            <AlertCircle className="w-8 h-8 text-red-500" />
          </div>
          <h3 className="text-lg font-medium text-dark-200 mb-2">Research Failed</h3>
          <p className="text-dark-400 text-sm">
            We encountered an error while researching this company. Please try again or delete the company.
          </p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-8 space-y-6 max-w-5xl">
      {/* Executive Summary */}
      {company.summary && (
        <section className="glass-card p-6">
          <h2 className="text-lg font-semibold text-dark-100 mb-3 flex items-center gap-2">
            <Lightbulb className="w-5 h-5 text-primary-400" />
            Executive Summary
          </h2>
          <p className="text-dark-300 leading-relaxed">{company.summary}</p>
        </section>
      )}

      {/* Key Facts Grid */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        <FactCard icon={Globe} label="Website" value={company.website || 'N/A'} />
        <FactCard icon={MapPin} label="Location" value={company.location || 'N/A'} />
        <FactCard icon={Briefcase} label="Industry" value={company.industry || 'N/A'} />
      </div>

      {/* Tech Stack */}
      {company.tech_stack && (
        <section className="glass-card p-6">
          <h2 className="text-lg font-semibold text-dark-100 mb-4 flex items-center gap-2">
            <Code2 className="w-5 h-5 text-primary-400" />
            Technology Stack
          </h2>
          <TechStackDisplay data={company.tech_stack} />
        </section>
      )}

      {/* Hiring Trends */}
      {company.hiring_trends && (
        <section className="glass-card p-6">
          <h2 className="text-lg font-semibold text-dark-100 mb-4 flex items-center gap-2">
            <TrendingUp className="w-5 h-5 text-primary-400" />
            Hiring Intelligence
          </h2>
          <HiringDisplay data={company.hiring_trends} />
        </section>
      )}

      {/* Synthesis Details */}
      {synthesis && (
        <>
          {synthesis.why_join && (
            <section className="glass-card p-6">
              <h2 className="text-lg font-semibold text-dark-100 mb-3">Why Join This Company</h2>
              <ul className="space-y-2">
                {synthesis.why_join.map((reason: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-dark-300">
                    <span className="text-primary-400 mt-1">+</span>
                    {reason}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {synthesis.potential_concerns && (
            <section className="glass-card p-6 border-amber-500/10">
              <h2 className="text-lg font-semibold text-dark-100 mb-3 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-amber-400" />
                Things to Consider
              </h2>
              <ul className="space-y-2">
                {synthesis.potential_concerns.map((concern: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-dark-300">
                    <span className="text-amber-400 mt-1">!</span>
                    {concern}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {synthesis.interview_talking_points && (
            <section className="glass-card p-6">
              <h2 className="text-lg font-semibold text-dark-100 mb-3">Interview Talking Points</h2>
              <ul className="space-y-2">
                {synthesis.interview_talking_points.map((point: string, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-dark-300">
                    <span className="text-emerald-400 mt-1">&bull;</span>
                    {point}
                  </li>
                ))}
              </ul>
            </section>
          )}

          {company.meta_data?.sources && company.meta_data.sources.length > 0 && (
            <section className="glass-card p-6">
              <h2 className="text-lg font-semibold text-dark-100 mb-3 flex items-center gap-2">
                <Globe className="w-5 h-5 text-primary-400" />
                Research Sources
              </h2>
              <ul className="space-y-2">
                {company.meta_data.sources.map((source: any, idx: number) => (
                  <li key={idx} className="flex items-start gap-2 text-dark-300">
                    <span className="text-primary-400 mt-1">&bull;</span>
                    <a href={source.url} target="_blank" rel="noopener noreferrer" className="hover:text-primary-400 underline decoration-primary-500/30">
                      {source.title || source.url}
                    </a>
                  </li>
                ))}
              </ul>
            </section>
          )}
        </>
      )}
    </div>
  );
}

function FactCard({ icon: Icon, label, value }: { icon: any; label: string; value: string }) {
  return (
    <div className="glass-card p-4">
      <div className="flex items-center gap-2 mb-1">
        <Icon className="w-4 h-4 text-dark-400" />
        <span className="text-xs text-dark-400 uppercase tracking-wide">{label}</span>
      </div>
      <p className="text-sm font-medium text-dark-200 truncate">{value}</p>
    </div>
  );
}

function TechStackDisplay({ data }: { data: Record<string, any> }) {
  const categories = ['languages', 'frameworks', 'databases', 'cloud_infrastructure', 'dev_tools', 'ai_ml'];

  return (
    <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
      {categories.map((cat) => {
        const items = data[cat];
        if (!items || !Array.isArray(items) || items.length === 0) return null;
        return (
          <div key={cat}>
            <h4 className="text-xs text-dark-400 uppercase tracking-wide mb-2">
              {cat.replace(/_/g, ' ')}
            </h4>
            <div className="flex flex-wrap gap-1.5">
              {items.map((item: any, idx: number) => (
                <span key={idx} className="badge-info">
                  {typeof item === 'string' ? item : item.name}
                </span>
              ))}
            </div>
          </div>
        );
      })}
    </div>
  );
}

function HiringDisplay({ data }: { data: Record<string, any> }) {
  return (
    <div className="space-y-3">
      {data.active_hiring !== undefined && (
        <div className="flex items-center gap-2">
          <span className={`w-2 h-2 rounded-full ${data.active_hiring ? 'bg-emerald-400' : 'bg-dark-500'}`} />
          <span className="text-sm text-dark-300">
            {data.active_hiring ? 'Actively hiring' : 'Not actively hiring'}
          </span>
        </div>
      )}
      {data.recent_job_areas && (
        <div>
          <h4 className="text-xs text-dark-400 uppercase tracking-wide mb-2">Hiring Areas</h4>
          <div className="flex flex-wrap gap-1.5">
            {data.recent_job_areas.map((area: string, idx: number) => (
              <span key={idx} className="badge-success">{area}</span>
            ))}
          </div>
        </div>
      )}
      {data.growth_indicators && (
        <div>
          <h4 className="text-xs text-dark-400 uppercase tracking-wide mb-2">Growth Signals</h4>
          <ul className="space-y-1">
            {data.growth_indicators.map((indicator: string, idx: number) => (
              <li key={idx} className="text-sm text-dark-300 flex items-center gap-2">
                <TrendingUp className="w-3 h-3 text-emerald-400" />
                {indicator}
              </li>
            ))}
          </ul>
        </div>
      )}
    </div>
  );
}
