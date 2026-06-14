import React, { useState } from 'react';
import { searchNLP } from '../api/client';

export default function NLPPanel({ onResults }) {
  const [query, setQuery] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);
  const [validationError, setValidationError] = useState(null);

  const MAX_CHARS = 1000;
  const MIN_CHARS = 3;

  const handleQueryChange = (e) => {
    const value = e.target.value;
    setQuery(value);

    // Clear validation error as user types
    if (validationError) {
      setValidationError(null);
    }
  };

  const validateInput = () => {
    if (query.length < MIN_CHARS || query.length > MAX_CHARS) {
      setValidationError('Keep your description between 3 and 1,000 characters.');
      return false;
    }
    return true;
  };

  const handleSubmit = async (e) => {
    e.preventDefault();

    if (!validateInput()) {
      return;
    }

    setIsLoading(true);
    setError(null);

    try {
      const data = await searchNLP(query);
      onResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  const isDisabled = isLoading || query.length < MIN_CHARS;

  return (
    <form onSubmit={handleSubmit} className="w-full">
      <div className="space-y-md">
        <div>
          <textarea
            value={query}
            onChange={handleQueryChange}
            placeholder="e.g. A dark sci-fi series with corporate conspiracies and a morally grey protagonist"
            maxLength={MAX_CHARS}
            rows={4}
            className="w-full p-md border-2 border-border-color rounded-md focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 bg-surface text-ink placeholder-muted resize-none"
            disabled={isLoading}
            aria-label="Anime description"
          />
          <div className="flex justify-between items-center mt-sm">
            <div className="text-xs text-muted">
              {query.length} / {MAX_CHARS}
            </div>
            {validationError && (
              <div className="text-xs text-danger">
                {validationError}
              </div>
            )}
          </div>
        </div>

        <button
          type="submit"
          disabled={isDisabled}
          className={`
            w-full py-md px-lg rounded-md font-semibold transition-all
            focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            ${
              isDisabled
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
      </div>
    </form>
  );
}
