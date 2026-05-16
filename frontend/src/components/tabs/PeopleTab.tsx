'use client';

import { useEffect } from 'react';
import { useStore } from '@/stores/useStore';
import { User, Linkedin, Star, Loader2 } from 'lucide-react';

export default function PeopleTab() {
  const { selectedCompany, people, loadingPeople, fetchPeople } = useStore();

  useEffect(() => {
    if (selectedCompany) {
      fetchPeople(selectedCompany.id);
    }
  }, [selectedCompany, fetchPeople]);

  if (loadingPeople) {
    return (
      <div className="flex items-center justify-center h-64">
        <Loader2 className="w-6 h-6 text-primary-400 animate-spin" />
      </div>
    );
  }

  if (people.length === 0) {
    return (
      <div className="p-8 text-center">
        <div className="w-16 h-16 mx-auto mb-4 rounded-2xl bg-dark-800 flex items-center justify-center">
          <User className="w-8 h-8 text-dark-500" />
        </div>
        <h3 className="text-lg font-medium text-dark-200 mb-2">No People Found</h3>
        <p className="text-dark-400 text-sm">
          People will be discovered during the research process.
        </p>
      </div>
    );
  }

  return (
    <div className="p-8 max-w-5xl">
      <h2 className="text-lg font-semibold text-dark-100 mb-4">
        Key People ({people.length})
      </h2>
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {people.map((person) => (
          <div key={person.id} className="glass-card-hover p-4">
            <div className="flex items-start gap-3">
              <div className="w-10 h-10 rounded-xl bg-dark-700/50 flex items-center justify-center flex-shrink-0">
                <User className="w-5 h-5 text-dark-400" />
              </div>
              <div className="flex-1 min-w-0">
                <div className="flex items-center gap-2">
                  <h3 className="text-sm font-medium text-dark-100 truncate">{person.name}</h3>
                  {person.relevance_score && person.relevance_score > 0.7 && (
                    <Star className="w-3 h-3 text-amber-400 flex-shrink-0" />
                  )}
                </div>
                <p className="text-xs text-dark-400 truncate">{person.title || 'Unknown role'}</p>
                {person.role_category && (
                  <span className="badge-info mt-1.5 text-[10px]">{person.role_category.replace(/_/g, ' ')}</span>
                )}
                {person.activity_summary && (
                  <p className="text-xs text-dark-300 mt-2 line-clamp-2">{person.activity_summary}</p>
                )}
              </div>
              {person.linkedin_url && (
                <a
                  href={person.linkedin_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="text-dark-500 hover:text-primary-400 transition-colors flex-shrink-0"
                >
                  <Linkedin className="w-4 h-4" />
                </a>
              )}
            </div>
            {person.relevance_score != null && (
              <div className="mt-3">
                <div className="flex items-center justify-between text-xs text-dark-400 mb-1">
                  <span>Relevance</span>
                  <span>{Math.round(person.relevance_score * 100)}%</span>
                </div>
                <div className="score-bar">
                  <div
                    className="score-fill bg-primary-500"
                    style={{ width: `${person.relevance_score * 100}%` }}
                  />
                </div>
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
