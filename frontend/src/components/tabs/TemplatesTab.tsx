'use client';

import { useEffect, useState } from 'react';
import { useStore } from '@/stores/useStore';
import { Mail, MessageSquare, Sparkles, Loader2, Copy, Check } from 'lucide-react';

const TEMPLATE_TYPES = [
  { value: 'email_cold_outreach', label: 'Cold Email', icon: Mail },
  { value: 'email_follow_up', label: 'Follow-up Email', icon: Mail },
  { value: 'linkedin_connection', label: 'LinkedIn Connection', icon: MessageSquare },
  { value: 'linkedin_message', label: 'LinkedIn DM', icon: MessageSquare },
  { value: 'interview_answer', label: 'Interview Answer', icon: Sparkles },
];

const TONES = ['professional', 'casual', 'bold', 'technical'];

export default function TemplatesTab() {
  const { selectedCompany, templates, loadingTemplates, fetchTemplates, generateTemplate } = useStore();
  const [selectedType, setSelectedType] = useState('email_cold_outreach');
  const [tone, setTone] = useState('professional');
  const [instructions, setInstructions] = useState('');
  const [copiedId, setCopiedId] = useState<string | null>(null);

  useEffect(() => {
    if (selectedCompany) {
      fetchTemplates(selectedCompany.id);
    }
  }, [selectedCompany, fetchTemplates]);

  const handleGenerate = async () => {
    if (!selectedCompany) return;
    await generateTemplate({
      company_id: selectedCompany.id,
      template_type: selectedType,
      tone,
      custom_instructions: instructions || undefined,
    });
  };

  const handleCopy = (id: string, content: string) => {
    navigator.clipboard.writeText(content);
    setCopiedId(id);
    setTimeout(() => setCopiedId(null), 2000);
  };

  return (
    <div className="p-8 max-w-5xl">
      {/* Generator */}
      <section className="glass-card p-6 mb-6">
        <h2 className="text-lg font-semibold text-dark-100 mb-4">Generate Template</h2>

        <div className="grid grid-cols-1 md:grid-cols-2 gap-4 mb-4">
          <div>
            <label className="text-xs text-dark-400 uppercase tracking-wide mb-1.5 block">Type</label>
            <select
              value={selectedType}
              onChange={(e) => setSelectedType(e.target.value)}
              className="input-field w-full"
            >
              {TEMPLATE_TYPES.map((t) => (
                <option key={t.value} value={t.value}>{t.label}</option>
              ))}
            </select>
          </div>

          <div>
            <label className="text-xs text-dark-400 uppercase tracking-wide mb-1.5 block">Tone</label>
            <div className="flex gap-2">
              {TONES.map((t) => (
                <button
                  key={t}
                  onClick={() => setTone(t)}
                  className={`px-3 py-2 rounded-lg text-xs font-medium transition-all ${
                    tone === t
                      ? 'bg-primary-600/20 text-primary-400 border border-primary-500/30'
                      : 'bg-dark-800 text-dark-400 hover:text-dark-200 border border-dark-700'
                  }`}
                >
                  {t}
                </button>
              ))}
            </div>
          </div>
        </div>

        <div className="mb-4">
          <label className="text-xs text-dark-400 uppercase tracking-wide mb-1.5 block">
            Custom Instructions (optional)
          </label>
          <textarea
            value={instructions}
            onChange={(e) => setInstructions(e.target.value)}
            placeholder={selectedType === 'interview_answer'
              ? 'Enter the interview question (e.g., "Why do you want to join us?")'
              : 'E.g., "Keep it under 3 sentences, mention my experience with React"'}
            className="input-field w-full h-20 resize-none"
          />
        </div>

        <button
          onClick={handleGenerate}
          disabled={loadingTemplates}
          className="btn-primary flex items-center gap-2"
        >
          {loadingTemplates ? <Loader2 className="w-4 h-4 animate-spin" /> : <Sparkles className="w-4 h-4" />}
          Generate
        </button>
      </section>

      {/* Generated Templates */}
      {templates.length > 0 && (
        <section>
          <h2 className="text-lg font-semibold text-dark-100 mb-4">
            Generated Templates ({templates.length})
          </h2>
          <div className="space-y-4">
            {templates.map((template) => (
              <div key={template.id} className="glass-card p-5">
                <div className="flex items-start justify-between mb-3">
                  <div>
                    <h3 className="text-sm font-medium text-dark-100">{template.title}</h3>
                    <div className="flex items-center gap-2 mt-1">
                      <span className="badge-info text-[10px]">{template.template_type.replace(/_/g, ' ')}</span>
                      {template.tone && <span className="badge text-[10px] bg-dark-800 text-dark-400">{template.tone}</span>}
                    </div>
                  </div>
                  <button
                    onClick={() => handleCopy(template.id, template.content)}
                    className="btn-ghost p-2"
                    title="Copy to clipboard"
                  >
                    {copiedId === template.id ? (
                      <Check className="w-4 h-4 text-emerald-400" />
                    ) : (
                      <Copy className="w-4 h-4" />
                    )}
                  </button>
                </div>
                <div className="bg-dark-800/50 rounded-xl p-4 text-sm text-dark-200 whitespace-pre-wrap leading-relaxed">
                  {template.content}
                </div>
              </div>
            ))}
          </div>
        </section>
      )}
    </div>
  );
}
