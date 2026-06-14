import React, { useState } from 'react';
import { ThumbsUp, ThumbsDown, Loader } from 'lucide-react';
import { submitFeedback } from '../api/client';

export default function FeedbackView({ animeTitle }) {
  const [vote, setVote] = useState(null); // null | 'up' | 'down'
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const isLocked = vote !== null; // Once voted, disable changes

  const handleVote = async (voteType) => {
    if (isLocked || isLoading) return;

    setIsLoading(true);
    setError(null);

    try {
      await submitFeedback(animeTitle, voteType);
      setVote(voteType);
    } catch (err) {
      setError('Couldn\'t save — try again');
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="flex flex-col gap-sm">
      <div className="flex gap-sm">
        {/* Upvote button */}
        <button
          onClick={() => handleVote('up')}
          disabled={isLoading || isLocked}
          className={`
            p-md rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            min-w-11 min-h-11
            ${
              isLoading || isLocked
                ? 'cursor-not-allowed'
                : 'hover:opacity-80'
            }
            ${
              vote === 'up'
                ? 'bg-surface-raised'
                : 'bg-transparent'
            }
          `}
          aria-label={`Upvote ${animeTitle}`}
        >
          <ThumbsUp
            className={`w-5 h-5 flex-shrink-0 ${
              vote === 'up'
                ? 'fill-success text-success'
                : 'text-muted'
            }`}
          />
        </button>

        {/* Downvote button */}
        <button
          onClick={() => handleVote('down')}
          disabled={isLoading || isLocked}
          className={`
            p-md rounded-md transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
            min-w-11 min-h-11
            ${
              isLoading || isLocked
                ? 'cursor-not-allowed'
                : 'hover:opacity-80'
            }
            ${
              vote === 'down'
                ? 'bg-surface-raised'
                : 'bg-transparent'
            }
          `}
          aria-label={`Downvote ${animeTitle}`}
        >
          <ThumbsDown
            className={`w-5 h-5 flex-shrink-0 ${
              vote === 'down'
                ? 'fill-danger text-danger'
                : 'text-muted'
            }`}
          />
        </button>

        {/* Loading spinner */}
        {isLoading && (
          <div className="flex items-center justify-center pl-sm">
            <Loader className="w-4 h-4 text-muted animate-spin" />
          </div>
        )}
      </div>

      {/* Error message */}
      {error && (
        <span className="text-xs text-danger">
          {error}
        </span>
      )}
    </div>
  );
}
