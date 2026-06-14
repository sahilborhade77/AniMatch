import React, { useState } from 'react';
import FeedbackView from './FeedbackView';

export default function DiscoveryGrid({
  results,
  isLoading,
  error,
  pathway,
  onSwitchPathway,
  onRetry,
}) {
  // Skeleton card component for loading state
  const SkeletonCard = () => (
    <div className="rounded-lg overflow-hidden shadow-card bg-surface-raised">
      <div className="w-full aspect-[2/3] bg-muted animate-pulse" />
      <div className="p-md space-y-sm">
        <div className="h-6 bg-muted animate-pulse rounded" />
        <div className="h-4 bg-muted animate-pulse rounded w-3/4" />
        <div className="space-y-xs">
          <div className="h-4 bg-muted animate-pulse rounded" />
          <div className="h-4 bg-muted animate-pulse rounded w-5/6" />
        </div>
      </div>
    </div>
  );

  // Result card component
  const ResultCard = ({ result }) => {
    const [imageError, setImageError] = useState(false);

    // Parse genres if it's a string
    const genreList = typeof result.genres === 'string'
      ? result.genres.split(',').map((g) => g.trim())
      : Array.isArray(result.genres)
        ? result.genres
        : [];

    return (
      <div className="rounded-lg overflow-hidden shadow-card bg-surface-raised">
        {/* Cover image */}
        <div className="w-full aspect-[2/3] overflow-hidden bg-muted">
          {imageError || !result.cover_image_url ? (
            <div className="w-full h-full bg-muted" />
          ) : (
            <img
              src={result.cover_image_url}
              alt={result.title}
              className="w-full h-full object-cover"
              onError={() => setImageError(true)}
              loading="lazy"
            />
          )}
        </div>

        {/* Card content */}
        <div className="p-md space-y-md flex flex-col h-full">
          {/* Title */}
          <h3 className="text-base font-semibold text-ink line-clamp-2">
            {result.title}
          </h3>

          {/* Genre tags */}
          {genreList.length > 0 && (
            <div className="flex gap-sm overflow-x-auto pb-sm scrollbar-thin">
              {genreList.map((genre) => (
                <span
                  key={genre}
                  className="flex-shrink-0 px-xs py-xs rounded-sm border border-border-color text-xs text-muted bg-surface"
                >
                  {genre}
                </span>
              ))}
            </div>
          )}

          {/* Synopsis */}
          <p className="text-sm text-muted line-clamp-3 flex-grow">
            {result.synopsis}
          </p>

          {/* Feedback */}
          <div className="pt-md border-t border-border-color mt-auto">
            <FeedbackView animeTitle={result.title} />
          </div>
        </div>
      </div>
    );
  };

  // Loading state: 6 skeleton cards
  if (isLoading) {
    return (
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
        {Array.from({ length: 6 }).map((_, i) => (
          <SkeletonCard key={i} />
        ))}
      </div>
    );
  }

  // Error state
  if (error) {
    return (
      <div className="flex flex-col items-center justify-center py-2xl space-y-lg">
        <div className="text-center max-w-md">
          <p className="text-danger text-sm mb-lg">
            {error}
          </p>
          {onRetry && (
            <button
              onClick={onRetry}
              className="py-md px-lg rounded-md bg-primary text-white font-semibold hover:opacity-90 transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
            >
              Try again
            </button>
          )}
        </div>
      </div>
    );
  }

  // Empty results state (only show if no results and not loading)
  if (!isLoading && results.length === 0) {
    return (
      <div className="flex flex-col items-center justify-center py-2xl space-y-lg">
        <div className="text-center max-w-md">
          <p className="text-muted text-sm mb-lg">
            Nothing matched that description. Try different words or use the quiz to explore.
          </p>
          <button
            onClick={() => onSwitchPathway('quiz')}
            className="py-md px-lg rounded-md bg-primary text-white font-semibold hover:opacity-90 transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2"
          >
            Try the quiz
          </button>
        </div>
      </div>
    );
  }

  // Results grid
  return (
    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-lg">
      {results.map((result, idx) => (
        <ResultCard key={`${result.title}-${idx}`} result={result} />
      ))}
    </div>
  );
}
