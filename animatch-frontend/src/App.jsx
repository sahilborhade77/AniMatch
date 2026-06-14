import React, { useState } from 'react';
import PathwayTabs from './components/PathwayTabs';
import NLPPanel from './components/NLPPanel';
import CrossMediaPanel from './components/CrossMediaPanel';
import QuizModule from './components/QuizModule';
import DiscoveryGrid from './components/DiscoveryGrid';

export default function App() {
  const [activePathway, setActivePathway] = useState('nlp');
  const [results, setResults] = useState([]);
  const [crossMediaMatch, setCrossMediaMatch] = useState(null);

  const handlePathwayChange = (pathway) => {
    setActivePathway(pathway);
    // Clear state when pathway changes
    setResults([]);
    setCrossMediaMatch(null);
  };

  const handleNLPResults = (resultArray) => {
    setResults(resultArray);
  };

  const handleCrossMediaResults = (resultArray, matchedTitle, matchedYear) => {
    setResults(resultArray);
    setCrossMediaMatch({ title: matchedTitle, year: matchedYear });
  };

  const handleQuizResults = (resultArray) => {
    setResults(resultArray);
  };

  const handleSwitchPathway = (pathway) => {
    handlePathwayChange(pathway);
  };

  return (
    <div className="min-h-screen bg-surface flex flex-col">
      {/* Header */}
      <header className="border-b border-border-color py-lg">
        <div className="max-w-5xl mx-auto px-md md:px-lg">
          <div className="flex justify-between items-center">
            <h1 className="text-2xl font-bold text-ink">AniMatch</h1>
            <p className="text-sm text-muted">Find your next favourite series</p>
          </div>
        </div>
      </header>

      {/* Main content */}
      <main className="flex-1 max-w-5xl w-full mx-auto px-md md:px-lg py-xl">
        <div className="space-y-xl">
          {/* Pathway tabs */}
          <PathwayTabs
            activePathway={activePathway}
            onSelect={handlePathwayChange}
          />

          {/* Active panel */}
          <div className="bg-surface-raised rounded-lg p-lg">
            {activePathway === 'nlp' && (
              <NLPPanel onResults={handleNLPResults} />
            )}
            {activePathway === 'crossmedia' && (
              <CrossMediaPanel onResults={handleCrossMediaResults} />
            )}
            {activePathway === 'quiz' && (
              <QuizModule onResults={handleQuizResults} />
            )}
          </div>

          {/* Cross-media match banner */}
          {crossMediaMatch && (
            <div className="p-md border-2 border-primary bg-surface-raised rounded-lg">
              <p className="text-ink font-semibold">
                Matched: {crossMediaMatch.title} ({crossMediaMatch.year})
              </p>
            </div>
          )}

          {/* Discovery grid */}
          <DiscoveryGrid
            results={results}
            isLoading={false}
            error={null}
            pathway={activePathway}
            onSwitchPathway={handleSwitchPathway}
          />
        </div>
      </main>

      {/* Footer */}
      <footer className="border-t border-border-color py-lg mt-auto">
        <div className="max-w-5xl mx-auto px-md md:px-lg">
          <p className="text-xs text-muted text-center">
            AniMatch v2.0 · Semantic anime discovery
          </p>
        </div>
      </footer>
    </div>
  );
}
