import React, { useState } from 'react';
import { searchCrossMedia } from '../api/client';

export default function CrossMediaPanel({ onResults }) {
  const [title, setTitle] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [matchedTitle, setMatchedTitle] = useState(null);
  const [matchedYear, setMatchedYear] = useState(null);

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!title.trim()) {
      return;
    }

    setIsLoading(true);
    setError(null);
    setMatchedTitle(null);
    setMatchedYear(null);

    try {
      const data = await searchCrossMedia(title);
      setMatchedTitle(data.matched_title);
      setMatchedYear(data.matched_year);
      onResults(data.results, data.matched_title, data.matched_year);
    } catch (err) {
      // Handle 404 (no match found) with custom message
      if (err.message && err.message.includes("couldn't find that title in our index")) {
        setError("We couldn't find that title. Try a different name — be specific (e.g. 'Inception' not 'that Leo DiCaprio dream movie').");
      } else {
        setError(err.message);
      }
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <form onSubmit={handleSubmit} className="w-full space-y-lg">
      <div className="space-y-sm">
        <label className="block text-sm font-semibold text-ink">
          Movie or TV show
        </label>
        <input
          type="text"
          value={title}
          onChange={(e) => setTitle(e.target.value)}
          placeholder="e.g. Interstellar, Breaking Bad, The Dark Knight"
          className="w-full p-md border-2 border-border-color rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 bg-surface text-ink placeholder-muted"
          disabled={isLoading}
          aria-label="Movie or TV show title"
        />
      </div>

      <button
        type="submit"
        disabled={isLoading || !title.trim()}
        className={`
          w-full py-md px-lg rounded-md font-semibold transition-all
          focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
          ${
            isLoading || !title.trim()
              ? 'bg-muted text-ink cursor-not-allowed opacity-50'
              : 'bg-primary text-white hover:opacity-90 active:opacity-100'
          }
        `}
      >
        {isLoading ? 'Finding matches…' : 'Find Anime'}
      </button>

      {error && (
        <div className="p-md bg-surface-raised border-l-4 border-danger rounded text-danger text-sm">
          {error}
        </div>
      )}

      {matchedTitle && matchedYear !== null && (
        <div className="p-md border-2 border-primary bg-surface-raised rounded-lg">
          <p className="text-ink font-semibold">
            Matched: {matchedTitle} ({matchedYear})
          </p>
        </div>
      )}
    </form>
  );
}
