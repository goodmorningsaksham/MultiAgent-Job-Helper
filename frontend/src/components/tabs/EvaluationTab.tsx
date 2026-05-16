'use client';

import { useEffect, useState } from 'react';
import { useStore } from '@/stores/useStore';
import api, { AgentRun } from '@/services/api';
import { BarChart3, Clock, Zap, AlertTriangle, CheckCircle2, Loader2 } from 'lucide-react';

export default function EvaluationTab() {
  const { selectedCompany } = useStore();
  const [agentRuns, setAgentRuns] = useState<AgentRun[]>([]);
  const [evaluations, setEvaluations] = useState<any[]>([]);
  const [loading, setLoading] = useState(true);

  const loadData = async () => {
    if (!selectedCompany) return;
    setLoading(true);
    const [runsRes, evalsRes] = await Promise.all([
      api.getAgentRuns(selectedCompany.id),
      api.getEvaluations(selectedCompany.id),
    ]);
    if (runsRes.ok) setAgentRuns(runsRes.data!);
    if (evalsRes.ok) setEvaluations(evalsRes.data!);
    setLoading(false);
  };

  useEffect(() => {
    if (!selectedCompany) return;
    loadData();
  }, [selectedCompany?.id]);

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-primary-400 animate-spin" />
      </div>
    );
  }

  const overallScores = calculateOverallScores(evaluations);

  return (
    <div className="p-8 max-w-5xl space-y-6">
      {/* Overall Scores */}
      <section className="glass-card p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4 flex items-center gap-2">
          <BarChart3 className="w-5 h-5 text-primary-400" />
          AI Quality Scores
        </h2>
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
          <ScoreCard
            label="Confidence"
            score={overallScores.confidence}
            description="How confident the AI is in its outputs"
          />
          <ScoreCard
            label="Source Grounding"
            score={overallScores.source_grounding}
            description="Claims backed by actual sources"
          />
          <ScoreCard
            label="Hallucination"
            score={1 - overallScores.hallucination}
            description="Lower hallucination = better"
            inverted
          />
          <ScoreCard
            label="Relevance"
            score={overallScores.relevance}
            description="How relevant outputs are to your needs"
          />
        </div>
      </section>

      {/* Agent Runs */}
      <section className="glass-card p-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4 flex items-center gap-2">
          <Zap className="w-5 h-5 text-primary-400" />
          Agent Activity ({agentRuns.length} runs)
        </h2>
        {agentRuns.length === 0 ? (
          <p className="text-dark-400 text-sm">No agent runs recorded yet.</p>
        ) : (
          <div className="space-y-2">
            {agentRuns.map((run) => (
              <div key={run.id} className="flex items-center gap-4 px-4 py-3 bg-dark-800/30 rounded-xl">
                <div className={`w-8 h-8 rounded-lg flex items-center justify-center ${
                  run.status === 'completed' ? 'bg-emerald-500/10' :
                  run.status === 'failed' ? 'bg-red-500/10' :
                  'bg-amber-500/10'
                }`}>
                  {run.status === 'completed' ? <CheckCircle2 className="w-4 h-4 text-emerald-400" /> :
                   run.status === 'failed' ? <AlertTriangle className="w-4 h-4 text-red-400" /> :
                   <Loader2 className="w-4 h-4 text-amber-400 animate-spin" />}
                </div>
                <div className="flex-1">
                  <p className="text-sm font-medium text-dark-200 capitalize">{run.agent_type} Agent</p>
                  <p className="text-xs text-dark-400">
                    {run.duration_ms ? `${(run.duration_ms / 1000).toFixed(1)}s` : 'Running'}
                    {run.tokens_used ? ` • ${run.tokens_used} tokens` : ''}
                  </p>
                </div>
                <span className={`badge text-[10px] ${
                  run.status === 'completed' ? 'badge-success' :
                  run.status === 'failed' ? 'badge-error' :
                  'badge-warning'
                }`}>
                  {run.status}
                </span>
              </div>
            ))}
          </div>
        )}
      </section>
    </div>
  );
}

function ScoreCard({ label, score, description, inverted }: {
  label: string;
  score: number;
  description: string;
  inverted?: boolean;
}) {
  const percentage = Math.round(score * 100);
  const color = percentage >= 70 ? 'text-emerald-400' :
                percentage >= 40 ? 'text-amber-400' : 'text-red-400';
  const bgColor = percentage >= 70 ? 'bg-emerald-400' :
                  percentage >= 40 ? 'bg-amber-400' : 'bg-red-400';

  return (
    <div className="bg-dark-800/30 rounded-xl p-4">
      <p className="text-xs text-dark-400 uppercase tracking-wide mb-2">{label}</p>
      <p className={`text-2xl font-bold ${color} mb-1`}>{percentage}%</p>
      <div className="score-bar mb-2">
        <div className={`score-fill ${bgColor}`} style={{ width: `${percentage}%` }} />
      </div>
      <p className="text-[10px] text-dark-500">{description}</p>
    </div>
  );
}

function calculateOverallScores(evaluations: any[]) {
  const metrics: Record<string, number[]> = {
    confidence: [],
    source_grounding: [],
    hallucination: [],
    relevance: [],
  };

  for (const eval_ of evaluations) {
    if (eval_.metric in metrics) {
      metrics[eval_.metric].push(eval_.score);
    }
  }

  return {
    confidence: average(metrics.confidence),
    source_grounding: average(metrics.source_grounding),
    hallucination: average(metrics.hallucination),
    relevance: average(metrics.relevance),
  };
}

function average(arr: number[]): number {
  if (arr.length === 0) return 0.5;
  return arr.reduce((a, b) => a + b, 0) / arr.length;
}
