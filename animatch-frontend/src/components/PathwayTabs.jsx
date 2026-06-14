import React from 'react';
import { MessageSquare, Film, ClipboardList } from 'lucide-react';

const pathways = [
  {
    id: 'nlp',
    label: 'Describe a vibe',
    subtext: "Tell us what you're in the mood for",
    icon: MessageSquare,
  },
  {
    id: 'crossmedia',
    label: 'Start with a movie or show',
    subtext: "We'll find anime with the same feel",
    icon: Film,
  },
  {
    id: 'quiz',
    label: 'Take the quiz',
    subtext: "Answer 5 questions and we'll match you",
    icon: ClipboardList,
  },
];

export default function PathwayTabs({ activePathway, onSelect }) {
  const handleSelect = (pathwayId) => {
    onSelect(pathwayId);
  };

  const handleKeyDown = (e, pathwayId) => {
    if (e.key === 'Enter' || e.key === ' ') {
      e.preventDefault();
      handleSelect(pathwayId);
    }
  };

  return (
    <div className="w-full">
      <div className="grid grid-cols-1 md:grid-cols-3 gap-lg">
        {pathways.map((pathway) => {
          const Icon = pathway.icon;
          const isActive = activePathway === pathway.id;

          return (
            <button
              key={pathway.id}
              onClick={() => handleSelect(pathway.id)}
              onKeyDown={(e) => handleKeyDown(e, pathway.id)}
              className={`
                p-lg rounded-lg text-left transition-all
                focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
                ${
                  isActive
                    ? 'border-2 border-primary bg-surface-raised shadow-card'
                    : 'border-2 border-border bg-surface-raised shadow-card hover:shadow-dropdown'
                }
              `}
              tabIndex={0}
              aria-pressed={isActive}
              aria-label={`${pathway.label}: ${pathway.subtext}`}
            >
              <div className="flex items-start gap-md">
                <Icon className="w-6 h-6 flex-shrink-0 mt-1 text-primary" />
                <div className="flex-1 min-w-0">
                  <h3 className="text-base font-semibold text-ink">
                    {pathway.label}
                  </h3>
                  <p className="text-sm text-muted mt-xs">
                    {pathway.subtext}
                  </p>
                </div>
              </div>
            </button>
          );
        })}
      </div>
    </div>
  );
}
