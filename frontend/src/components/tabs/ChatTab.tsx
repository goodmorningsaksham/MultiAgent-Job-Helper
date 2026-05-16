'use client';

import { useState, useRef, useEffect } from 'react';
import { useStore } from '@/stores/useStore';
import { Send, Loader2, Bot, User, ExternalLink } from 'lucide-react';

export default function ChatTab() {
  const { selectedCompany, messages, loadingChat, sendChatMessage } = useStore();
  const [input, setInput] = useState('');
  const messagesEndRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  const handleSend = async () => {
    if (!input.trim() || !selectedCompany || loadingChat) return;
    const message = input;
    setInput('');
    await sendChatMessage(selectedCompany.id, message);
  };

  const SUGGESTIONS = [
    "Why should I join this company?",
    "What's their engineering culture like?",
    "Help me prepare for a technical interview here",
    "What are good talking points for a conversation with their team?",
  ];

  return (
    <div className="flex flex-col h-[calc(100vh-200px)]">
      {/* Messages */}
      <div className="flex-1 overflow-y-auto scrollbar-thin px-8 py-6">
        {messages.length === 0 ? (
          <div className="flex flex-col items-center justify-center h-full">
            <div className="w-16 h-16 rounded-2xl bg-primary-600/10 flex items-center justify-center mb-4">
              <Bot className="w-8 h-8 text-primary-400" />
            </div>
            <h3 className="text-lg font-medium text-dark-200 mb-2">AI Research Assistant</h3>
            <p className="text-dark-400 text-sm text-center max-w-md mb-6">
              Ask me anything about {selectedCompany?.name}. I&apos;ll use the research data to give you grounded answers.
            </p>
            <div className="grid grid-cols-1 md:grid-cols-2 gap-2 max-w-lg">
              {SUGGESTIONS.map((suggestion, idx) => (
                <button
                  key={idx}
                  onClick={() => setInput(suggestion)}
                  className="text-left text-xs text-dark-400 hover:text-dark-200 bg-dark-800/50 hover:bg-dark-800 border border-dark-700/50 rounded-xl px-3 py-2.5 transition-all"
                >
                  {suggestion}
                </button>
              ))}
            </div>
          </div>
        ) : (
          <div className="space-y-4 max-w-3xl mx-auto">
            {messages.map((msg) => (
              <div key={msg.id} className={`flex gap-3 ${msg.role === 'user' ? 'justify-end' : ''}`}>
                {msg.role === 'assistant' && (
                  <div className="w-8 h-8 rounded-lg bg-primary-600/10 flex items-center justify-center flex-shrink-0">
                    <Bot className="w-4 h-4 text-primary-400" />
                  </div>
                )}
                <div className={`max-w-[80%] ${
                  msg.role === 'user'
                    ? 'bg-primary-600/20 border border-primary-500/20 rounded-2xl rounded-br-md px-4 py-3'
                    : 'bg-dark-800/50 border border-dark-700/30 rounded-2xl rounded-bl-md px-4 py-3'
                }`}>
                  <p className="text-sm text-dark-200 whitespace-pre-wrap leading-relaxed">{msg.content}</p>
                  {msg.sources_used && msg.sources_used.length > 0 && (
                    <div className="mt-2 pt-2 border-t border-dark-700/30">
                      <p className="text-[10px] text-dark-500 uppercase tracking-wide mb-1">Sources</p>
                      <div className="flex flex-wrap gap-1">
                        {msg.sources_used.slice(0, 3).map((source: any, idx: number) => (
                          <a
                            key={idx}
                            href={source.url}
                            target="_blank"
                            rel="noopener noreferrer"
                            className="inline-flex items-center gap-1 text-[10px] text-primary-400 hover:text-primary-300"
                          >
                            <ExternalLink className="w-2.5 h-2.5" />
                            {source.title?.slice(0, 30) || 'Source'}
                          </a>
                        ))}
                      </div>
                    </div>
                  )}
                  {msg.evaluation_scores && (
                    <div className="mt-2 pt-2 border-t border-dark-700/30 flex items-center gap-3">
                      <ScorePill label="Confidence" score={msg.evaluation_scores.confidence_score} />
                      <ScorePill label="Grounding" score={msg.evaluation_scores.source_grounding_score} />
                    </div>
                  )}
                </div>
                {msg.role === 'user' && (
                  <div className="w-8 h-8 rounded-lg bg-dark-700/50 flex items-center justify-center flex-shrink-0">
                    <User className="w-4 h-4 text-dark-400" />
                  </div>
                )}
              </div>
            ))}
            {loadingChat && (
              <div className="flex gap-3">
                <div className="w-8 h-8 rounded-lg bg-primary-600/10 flex items-center justify-center">
                  <Bot className="w-4 h-4 text-primary-400" />
                </div>
                <div className="bg-dark-800/50 border border-dark-700/30 rounded-2xl rounded-bl-md px-4 py-3">
                  <Loader2 className="w-4 h-4 text-dark-400 animate-spin" />
                </div>
              </div>
            )}
            <div ref={messagesEndRef} />
          </div>
        )}
      </div>

      {/* Input */}
      <div className="px-8 py-4 border-t border-dark-700/50 bg-dark-900/30">
        <div className="max-w-3xl mx-auto flex items-center gap-3">
          <input
            type="text"
            value={input}
            onChange={(e) => setInput(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && !e.shiftKey && handleSend()}
            placeholder="Ask about this company..."
            className="input-field flex-1"
            disabled={loadingChat}
          />
          <button
            onClick={handleSend}
            disabled={!input.trim() || loadingChat}
            className="btn-primary p-3"
          >
            <Send className="w-4 h-4" />
          </button>
        </div>
      </div>
    </div>
  );
}

function ScorePill({ label, score }: { label: string; score?: number }) {
  if (score == null) return null;
  const percentage = Math.round(score * 100);
  const color = percentage >= 70 ? 'text-emerald-400' : percentage >= 40 ? 'text-amber-400' : 'text-red-400';
  return (
    <span className={`text-[10px] ${color}`}>
      {label}: {percentage}%
    </span>
  );
}
