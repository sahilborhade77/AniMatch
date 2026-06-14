const BASE_URL = import.meta.env.VITE_API_BASE_URL || 'http://localhost:8000';

/**
 * Helper function to make API requests with consistent error handling
 */
async function makeRequest(endpoint, body) {
  const response = await fetch(`${BASE_URL}${endpoint}`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify(body),
  });

  if (!response.ok) {
    const data = await response.json();
    throw new Error(data.error || 'Something went wrong');
  }

  return response.json();
}

/**
 * Search using natural language processing
 * @param {string} query - The search query
 * @returns {Promise<{results}>} Search results
 */
export async function searchNLP(query) {
  return makeRequest('/search/nlp', { query });
}

/**
 * Search across multiple media types
 * @param {string} title - The title to search for
 * @returns {Promise<{matched_title, matched_year, results}>} Matched media and results
 */
export async function searchCrossMedia(title) {
  return makeRequest('/search/crossmedia', { title });
}

/**
 * Search based on quiz answers
 * @param {object} answers - Quiz answers object
 * @returns {Promise<{synthesized_prompt, results}>} Synthesized prompt and results
 */
export async function searchQuiz(answers) {
  return makeRequest('/search/quiz', answers);
}

/**
 * Submit feedback for an anime
 * @param {string} anime_title - The anime title to provide feedback for
 * @param {"up"|"down"} vote - Vote type: "up" for upvote, "down" for downvote
 * @returns {Promise<{message}>} Feedback submission response
 */
export async function submitFeedback(anime_title, vote) {
  return makeRequest('/feedback', { anime_title, vote });
}
