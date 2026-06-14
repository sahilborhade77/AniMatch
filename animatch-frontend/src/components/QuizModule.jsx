import React, { useState } from 'react';
import { ChevronLeft } from 'lucide-react';
import { searchQuiz } from '../api/client';

const steps = [
  {
    key: 'pacing',
    question: 'How fast do you like the story to move?',
    options: ['Slow burn', 'Steady build', 'Fast-paced', 'Breakneck speed'],
  },
  {
    key: 'tone',
    question: "What's the mood you're after?",
    options: ['Dark and heavy', 'Tense and serious', 'Balanced', 'Light and fun'],
  },
  {
    key: 'narrative_focus',
    question: 'What should the story centre on?',
    options: ['Character growth', 'Romance', 'Action and battles', 'Mystery and twists', 'World-building'],
  },
  {
    key: 'setting',
    question: 'Where should it take place?',
    options: ['Real-world modern', 'Feudal / historical', 'Fantasy world', 'Sci-fi / futuristic', 'Post-apocalyptic'],
  },
  {
    key: 'stakes',
    question: 'How high should the stakes be?',
    options: ['World-ending', 'Life and death', 'Personal and emotional', 'Low stakes / slice of life'],
  },
];

export default function QuizModule({ onResults }) {
  const [currentStep, setCurrentStep] = useState(0);
  const [answers, setAnswers] = useState({});
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState(null);

  const step = steps[currentStep];
  const isAnswered = answers[step.key];
  const progress = currentStep + 1;

  const handleSelectOption = (option) => {
    setAnswers({
      ...answers,
      [step.key]: option,
    });
  };

  const handleNext = () => {
    if (currentStep < steps.length - 1) {
      setCurrentStep(currentStep + 1);
    }
  };

  const handleBack = () => {
    if (currentStep > 0) {
      setCurrentStep(currentStep - 1);
    }
  };

  const handleSubmit = async () => {
    setIsLoading(true);
    setError(null);

    try {
      const data = await searchQuiz(answers);
      onResults(data.results);
    } catch (err) {
      setError(err.message);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="w-full space-y-xl">
      {/* Progress bar */}
      <div className="space-y-sm">
        <div className="text-xs text-muted">
          Step {progress} of 5
        </div>
        <div className="w-full h-1 bg-border-color rounded-full overflow-hidden">
          <div
            className="h-full bg-primary transition-all duration-300"
            style={{ width: `${(progress / 5) * 100}%` }}
          />
        </div>
      </div>

      {/* Question */}
      <div>
        <h2 className="text-lg font-semibold text-ink">
          {step.question}
        </h2>
      </div>

      {/* Options grid */}
      <div className="space-y-md">
        {step.options.map((option) => (
          <button
            key={option}
            onClick={() => handleSelectOption(option)}
            className={`
              w-full p-lg rounded-lg border-2 transition-all text-left
              focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
              min-h-16
              ${
                isAnswered === option
                  ? 'border-primary bg-surface-raised'
                  : 'border-border-color bg-surface hover:border-primary hover:bg-surface-raised'
              }
            `}
          >
            <span className="text-base font-medium text-ink">
              {option}
            </span>
          </button>
        ))}
      </div>

      {/* Error message */}
      {error && (
        <div className="p-md bg-surface-raised border-l-4 border-danger rounded text-danger text-sm">
          {error}
        </div>
      )}

      {/* Navigation buttons */}
      <div className="flex gap-md pt-lg">
        {currentStep > 0 && (
          <button
            onClick={handleBack}
            className="py-md px-lg rounded-lg border-2 border-border-color text-ink font-semibold hover:border-primary transition-all focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2 flex items-center gap-sm"
          >
            <ChevronLeft className="w-5 h-5" />
            Back
          </button>
        )}

        {currentStep === steps.length - 1 ? (
          <button
            onClick={handleSubmit}
            disabled={!isAnswered || isLoading}
            className={`
              flex-1 py-md px-lg rounded-lg font-semibold transition-all
              focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
              ${
                !isAnswered || isLoading
                  ? 'bg-muted text-ink cursor-not-allowed opacity-50'
                  : 'bg-primary text-white hover:opacity-90 active:opacity-100'
              }
            `}
          >
            {isLoading ? 'Finding matches…' : 'Find Anime'}
          </button>
        ) : (
          <button
            onClick={handleNext}
            disabled={!isAnswered}
            className={`
              flex-1 py-md px-lg rounded-lg font-semibold transition-all
              focus:outline-none focus:ring-2 focus:ring-primary focus:ring-offset-2
              ${
                !isAnswered
                  ? 'bg-muted text-ink cursor-not-allowed opacity-50'
                  : 'bg-primary text-white hover:opacity-90 active:opacity-100'
              }
            `}
          >
            Next
          </button>
        )}
      </div>
    </div>
  );
}
