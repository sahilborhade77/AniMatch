# AniMatch v2.0 — Full Build Prompt List
> Mapped to actual file structure. Run in order — each prompt builds on the last.

---

## PHASE 1 — BACKEND FOUNDATION

### Prompt 1 — `animatch-backend/app/config.py`

```
Create /animatch-backend/app/config.py for AniMatch v2.0 FastAPI backend.

Use pydantic-settings BaseSettings to load all environment variables from a .env file:
- QDRANT_URL: str
- QDRANT_API_KEY: str
- SUPABASE_URL: str
- SUPABASE_KEY: str
- JWT_SECRET: str
- FRONTEND_URL: str (used for CORS origin locking)
- COLLECTION_NAME: str = "animatch"
- TOP_K: int = 10

Expose a single settings = Settings() instance imported everywhere else.
No secrets hardcoded anywhere. Include a .env.example file listing all keys with placeholder values.
```

---

### Prompt 2 — `animatch-backend/app/inference.py`

```
Create /animatch-backend/app/inference.py for AniMatch v2.0.

Requirements:
- Load the ONNX model from /animatch-backend/app/models/model.onnx using onnxruntime.InferenceSession
- Use the tokenizer from tokenizers library (tokenizer.json saved alongside model.onnx) — no transformers, no torch at runtime
- Expose a single function: encode(text: str) -> list[float]
- The function must: tokenize the input text, run the ONNX session, apply mean pooling over token embeddings, L2-normalize the output, and return a Python list of 384 floats
- The InferenceSession must be loaded once at module import time (singleton) — never re-loaded per request
- Total runtime memory footprint must stay under 120MB
- No PyTorch. No Hugging Face transformers pipeline. No sentence-transformers library at runtime.

Also write a __main__ block that encodes the string "test query" and prints the vector length to verify the module works standalone.
```

---

### Prompt 3 — `animatch-backend/app/auth.py`

```
Create /animatch-backend/app/auth.py for AniMatch v2.0.

Requirements:
- Use python-jose with HS256 algorithm
- Read JWT_SECRET from config.py settings
- Expose:
  - create_access_token(data: dict, expires_minutes: int = 60) -> str
  - verify_token(token: str) -> dict  (raises HTTPException 401 on invalid/expired)
  - require_admin: a FastAPI Depends() dependency that extracts Bearer token from Authorization header, calls verify_token, and returns the decoded payload
- If the token is missing, malformed, or expired, always return HTTP 401 with a clear message — never 403
- Do not store tokens server-side — fully stateless HS256 verification only
```

---

### Prompt 4 — `animatch-backend/app/qdrant_client.py`

```
Create /animatch-backend/app/qdrant_client.py for AniMatch v2.0.

Requirements:
- Use the qdrant-client Python SDK
- Initialize QdrantClient once at module level using QDRANT_URL and QDRANT_API_KEY from config.py settings
- Expose one async-compatible function:
  search_vectors(vector: list[float], top_k: int = 10) -> list[dict]
  - Queries the collection named settings.COLLECTION_NAME
  - Uses Cosine distance (already set on the collection)
  - Returns a list of dicts, each containing: title, genres, studio, synopsis, cover_image_url (from payload) and score (float, 0–1)
- Handle QdrantClient connection errors gracefully — raise HTTPException 503 with message "Search service unavailable. Try again shortly."
```

---

### Prompt 5 — `animatch-backend/app/main.py`

```
Create /animatch-backend/app/main.py for AniMatch v2.0 FastAPI application.

Requirements:
- FastAPI app with title "AniMatch API" and version "2.0"
- CORS middleware: allow_origins=[settings.FRONTEND_URL], allow_methods=["POST", "GET"], allow_headers=["Authorization", "Content-Type"] — no wildcard origins ever
- Mount routers (to be created separately):
  - /search/nlp
  - /search/crossmedia
  - /search/quiz
  - /feedback
  - /admin
- GET /health returns {"status": "ok", "version": "2.0"} — no auth required, used by Render health checks
- Global exception handler: catch unhandled Exception, log it, return HTTP 500 with {"error": "An unexpected error occurred. Please try again."} — never expose stack traces to the client
- Startup event: log that the ONNX model is loaded and Qdrant client is ready
```

---

### Prompt 6 — `animatch-backend/Run.sh`

```
Create /animatch-backend/Run.sh — the Render startup script for AniMatch v2.0 backend.

Requirements:
- Activate virtual environment if it exists
- Run: uvicorn app.main:app --host 0.0.0.0 --port $PORT --workers 1
- Use only 1 worker — multiple workers would each load the ONNX model into memory, exceeding the 120MB budget
- Make the script executable (chmod +x)
- Add a comment block at the top explaining the single-worker constraint
```

---

### Prompt 7 — `animatch-backend/requirements.txt`

```
Create /animatch-backend/requirements.txt for AniMatch v2.0 backend.

Must include exact pinned versions of:
- fastapi
- uvicorn[standard]
- pydantic
- pydantic-settings
- onnxruntime
- tokenizers
- qdrant-client
- supabase
- python-jose[cryptography]
- python-dotenv
- httpx (for async Supabase REST calls)

Must explicitly NOT include:
- torch
- tensorflow
- transformers
- sentence-transformers

Add a comment at the top: "# torch and transformers are excluded — ONNX runtime only. Adding them will exceed the 120MB memory budget."
```

---

## PHASE 2 — BACKEND ROUTES

### Prompt 8 — NLP Search Route

```
Create /animatch-backend/app/routes/nlp.py for AniMatch v2.0.

Requirements:
- APIRouter with prefix /search/nlp
- POST / accepts JSON body: { "query": string } — min 3 chars, max 1000 chars (Pydantic validator, reject with HTTP 422 and clear message if violated)
- Flow:
  1. Take the raw query string
  2. Prepend "Title: . Genres: . Studio: . Synopsis: " + query (apply enrichment format even for free-text queries so the vector space aligns with indexed records)
  3. Call encode() from inference.py to get a 384-dim vector
  4. Call search_vectors() from qdrant_client.py
  5. Return: { "results": [ { title, genres, studio, synopsis, cover_image_url, score } ] }
- All async. If encode() or search_vectors() raises, return HTTP 503 with "Search is temporarily unavailable. Try again shortly."
- Response must always be an array — never return a single object
```

---

### Prompt 9 — Cross-Media Search Route

```
Create /animatch-backend/app/routes/crossmedia.py for AniMatch v2.0.

Requirements:
- APIRouter with prefix /search/crossmedia
- POST / accepts JSON body: { "title": string } — min 3 chars, max 1000 chars
- Local IMDb baseline index lives at /animatch-backend/app/data/imdb_index.json
  Format: [ { "title": str, "year": int, "synopsis": str }, ... ]
  Load it once at module level — never re-read per request
- Flow:
  1. Fuzzy-match the submitted title against the index (case-insensitive, partial match acceptable)
  2. If no match found: return HTTP 404 with { "error": "We couldn't find that title in our index. Try a different movie or show name." }
  3. If matched: extract the synopsis
  4. Build enriched string: "Title: {matched_title}. Genres: . Studio: . Synopsis: {synopsis}"
  5. encode() → search_vectors() → return results
- Response shape: { "matched_title": str, "matched_year": int, "results": [ { title, genres, studio, synopsis, cover_image_url, score } ] }
- The matched_title and matched_year are displayed in the frontend confirmation banner before results appear
```

---

### Prompt 10 — Quiz Search Route

```
Create /animatch-backend/app/routes/quiz.py for AniMatch v2.0.

Requirements:
- APIRouter with prefix /search/quiz
- POST / accepts JSON body with exactly 5 fields (all str, min 2 chars each):
  - pacing: e.g. "slow burn" / "fast-paced"
  - tone: e.g. "dark and serious" / "lighthearted"
  - narrative_focus: e.g. "character development" / "action and fights"
  - setting: e.g. "futuristic sci-fi" / "feudal Japan"
  - stakes: e.g. "world-ending consequences" / "personal and intimate"
- Flow:
  1. Synthesize the 5 fields into a single descriptive paragraph:
     "A {pacing} series with a {tone} tone, focused on {narrative_focus}, set in a {setting} world, with {stakes} at stake."
  2. Build enriched string: "Title: . Genres: . Studio: . Synopsis: {synthesized_paragraph}"
  3. encode() → search_vectors() → return results
- Response: { "synthesized_prompt": str, "results": [ { title, genres, studio, synopsis, cover_image_url, score } ] }
- Include synthesized_prompt in the response so the frontend can optionally display "We searched for: ..." for transparency
```

---

### Prompt 11 — Feedback Route

```
Create /animatch-backend/app/routes/feedback.py for AniMatch v2.0.

Requirements:
- APIRouter with prefix /feedback
- POST / accepts JSON body: { "anime_title": str, "vote": "up" | "down" }
  - anime_title: min 1 char, max 500 chars
  - vote: must be exactly "up" or "down" — reject anything else with HTTP 422
- Flow:
  1. Build payload: { anime_title, vote, created_at: ISO timestamp }
  2. POST to Supabase REST endpoint: {SUPABASE_URL}/rest/v1/votes
  3. Use headers: apikey: SUPABASE_KEY, Authorization: Bearer SUPABASE_KEY, Content-Type: application/json, Prefer: return=minimal
  4. If Supabase returns non-2xx: log the error, return HTTP 503 "We couldn't save your feedback right now."
  5. On success: return HTTP 200 { "message": "Feedback recorded." }
- Use httpx.AsyncClient for the Supabase call — never blocking requests library
- No auth required on this endpoint — public POST
```

---

### Prompt 12 — Admin Route

```
Create /animatch-backend/app/routes/admin.py for AniMatch v2.0.

Requirements:
- APIRouter with prefix /admin
- All routes protected by require_admin dependency from auth.py
- GET /votes — fetch all rows from Supabase votes table via REST GET {SUPABASE_URL}/rest/v1/votes?select=*
  - Use service key header: apikey: SUPABASE_KEY
  - Return the raw array of vote records
- GET /votes/summary — return aggregated counts:
  { "total": int, "upvotes": int, "downvotes": int, "top_upvoted": [ {anime_title, count} ] (top 10) }
  Compute this from the Supabase response in Python — do not use a Supabase RPC
- All Supabase calls use httpx.AsyncClient
```

---

## PHASE 3 — ML SCRIPTS (run locally, never deployed)

### Prompt 13 — ONNX Export Script

```
Create /animatch-backend/scripts/export_onnx.py — a one-time local script, never deployed to Render.

Requirements:
- Load all-MiniLM-L6-v2 from sentence-transformers
- Export the model to ONNX format at /animatch-backend/app/models/model.onnx
- Also save the tokenizer vocabulary as /animatch-backend/app/models/tokenizer.json using the tokenizers library format (so runtime inference.py can load it without transformers)
- Print: "Model exported to model.onnx — {file size in MB}" on success
- This script requires torch and sentence-transformers locally — add a comment warning these must NOT be in requirements.txt
```

---

### Prompt 14 — Dataset Vectorization Script

```
Create /animatch-backend/scripts/vectorize_dataset.py — a one-time local script, never deployed.

Requirements:
- Load the anime dataset from /data set/MyAnimeList Dataset.zip (extract and read the CSV inside)
- For each record apply the enrichment formula:
  "Title: {title}. Genres: {genres}. Studio: {studio}. Synopsis: {synopsis}"
- Encode each enriched string using encode() from inference.py → 384-dim vector
- Upload to Qdrant collection "animatch" in batches of 100:
  - Point ID: integer index
  - Vector: 384-dim float list
  - Payload: { title, genres, studio, synopsis, cover_image_url }
- Create the collection first if it doesn't exist (Cosine distance, vector size 384)
- Print progress every 500 records: "Uploaded 500/19000..."
- Print total time on completion
- Read QDRANT_URL and QDRANT_API_KEY from .env file
- Handle missing cover_image_url gracefully — use empty string as default
```

---

## PHASE 4 — FRONTEND

### Prompt 15 — `animatch-frontend/tailwind.config.js`

```
Configure /animatch-frontend/tailwind.config.js for AniMatch v2.0.

Add custom design tokens under theme.extend:

Colors (as CSS variable references):
- primary: var(--color-primary)
- ink: var(--color-ink)
- muted: var(--color-muted)
- surface: var(--color-surface)
- surface-raised: var(--color-surface-raised)
- border-color: var(--color-border)
- success: var(--color-success)
- warning: var(--color-warning)
- danger: var(--color-danger)

Spacing (extend, not replace):
- xs: 4px, sm: 8px, md: 16px, lg: 24px, xl: 40px, 2xl: 64px

Border radius:
- radius-sm: 6px, radius-md: 10px, radius-lg: 16px

Box shadow:
- shadow-card: (resting card shadow)
- shadow-dropdown: (dropdown/hover shadow)
- shadow-modal: (modal shadow)

Also add the CSS variable definitions to /animatch-frontend/src/index.css under :root so all tokens resolve correctly. Use a dark, anime-appropriate color palette — deep navy/dark backgrounds, vibrant accent.
```

---

### Prompt 16 — `animatch-frontend/src/api/client.js`

```
Create /animatch-frontend/src/api/client.js — the single API client for AniMatch v2.0 frontend.

Requirements:
- Read base URL from import.meta.env.VITE_API_BASE_URL
- Expose async functions (all use fetch, all handle errors consistently):
  - searchNLP(query: string) → POST /search/nlp → returns { results }
  - searchCrossMedia(title: string) → POST /search/crossmedia → returns { matched_title, matched_year, results }
  - searchQuiz(answers: object) → POST /search/quiz → returns { synthesized_prompt, results }
  - submitFeedback(anime_title: string, vote: "up"|"down") → POST /feedback → returns { message }
- All functions: set Content-Type: application/json, JSON.stringify the body
- Error handling: if response is not ok, parse the error JSON and throw new Error(data.error || "Something went wrong") — the component handles display
- No other file in the frontend should call fetch directly — all API calls go through this client
```

---

### Prompt 17 — `animatch-frontend/src/components/PathwayTabs.jsx`

```
Create /animatch-frontend/src/components/PathwayTabs.jsx for AniMatch v2.0.

Requirements:
- Three large selectable cards displayed horizontally on desktop, stacked on mobile
- Options:
  - "Describe a vibe" (value: "nlp") — subtext: "Tell us what you're in the mood for"
  - "Start with a movie or show" (value: "crossmedia") — subtext: "We'll find anime with the same feel"
  - "Take the quiz" (value: "quiz") — subtext: "Answer 5 questions and we'll match you"
- Props: activePathway (string), onSelect (function)
- Active card: visually distinct — border in primary color, background surface-raised, not just a color tint change
- Use Lucide icons: MessageSquare for nlp, Film for crossmedia, ClipboardList for quiz
- Fully keyboard accessible — Enter and Space activate a card
- Use radius-lg, shadow-card tokens
- Sentence case on all text. No periods on labels.
```

---

### Prompt 18 — NLP Panel (inside App.jsx or separate component)

```
Create the NLP search panel as /animatch-frontend/src/components/NLPPanel.jsx for AniMatch v2.0.

Requirements:
- A textarea (not a single-line input) — users write descriptive queries
- Placeholder: "e.g. A dark sci-fi series with corporate conspiracies and a morally grey protagonist"
- Character counter shown below textarea: "142 / 1000"
- Client-side validation before submit: min 3 chars — show inline error "Keep your description between 3 and 1,000 characters." — never an alert()
- "Find Anime" button — disabled while loading or while input < 3 chars
- Loading state: button shows "Finding matches…" and is disabled — spinner optional
- On error from API: show error message inline below the button — never a modal, never an alert
- Props: onResults(results: array) — called when search succeeds
- Uses searchNLP() from api/client.js
```

---

### Prompt 19 — Cross-Media Panel

```
Create /animatch-frontend/src/components/CrossMediaPanel.jsx for AniMatch v2.0.

Requirements:
- Single text input: placeholder "e.g. Interstellar, Breaking Bad, The Dark Knight"
- Label above input (always visible, never placeholder-as-label): "Movie or TV show"
- "Find Anime" button — disabled while loading
- Loading state: "Finding matches…"
- On success: show a confirmation banner ABOVE the results:
  "Matched: {matched_title} ({matched_year})" — styled distinctly (primary color border, surface-raised background)
- On 404 (no match): show inline message "We couldn't find that title. Try a different name — be specific (e.g. 'Inception' not 'that Leo DiCaprio dream movie')."
- On other error: show the API error message inline
- Props: onResults(results: array, matchedTitle: string, matchedYear: number)
- Uses searchCrossMedia() from api/client.js
```

---

### Prompt 20 — `animatch-frontend/src/components/QuizModule.jsx`

```
Create /animatch-frontend/src/components/QuizModule.jsx for AniMatch v2.0.

Requirements:
- 5 steps, one question per step (do NOT show all questions at once)
- Questions and options:
  Step 1 — Pacing: "How fast do you like the story to move?"
    Options: Slow burn | Steady build | Fast-paced | Breakneck speed
  Step 2 — Tone: "What's the mood you're after?"
    Options: Dark and heavy | Tense and serious | Balanced | Light and fun
  Step 3 — Narrative Focus: "What should the story centre on?"
    Options: Character growth | Romance | Action and battles | Mystery and twists | World-building
  Step 4 — Setting: "Where should it take place?"
    Options: Real-world modern | Feudal / historical | Fantasy world | Sci-fi / futuristic | Post-apocalyptic
  Step 5 — Stakes: "How high should the stakes be?"
    Options: World-ending | Life and death | Personal and emotional | Low stakes / slice of life

- Each option is a large clickable card (min 44×44px tap target) — NOT a radio button or checkbox
- Selected option: visually highlighted with primary color border
- Progress bar at top: "Step 2 of 5"
- Back button on steps 2–5
- "Find Anime" button only appears on step 5, after an option is selected
- Loading state on submit: "Finding matches…"
- Props: onResults(results: array)
- Uses searchQuiz() from api/client.js, passing { pacing, tone, narrative_focus, setting, stakes }
```

---

### Prompt 21 — `animatch-frontend/src/components/FeedbackView.jsx`

```
Create /animatch-frontend/src/components/FeedbackView.jsx for AniMatch v2.0.

This component is the upvote/downvote control embedded inside each result card.

Requirements:
- Props: animeTitle (string)
- Two buttons: thumbs up (Lucide ThumbsUp icon) and thumbs down (Lucide ThumbsDown icon)
- BOTH icon and color used to convey state — never color alone (accessibility rule)
- States:
  - Default: both buttons neutral (muted color)
  - Upvoted: thumbs up button filled success color, thumbs down neutral
  - Downvoted: thumbs down filled danger color, thumbs up neutral
  - Loading: both buttons disabled, show a small spinner
  - Error: show tiny inline text below buttons "Couldn't save — try again" in danger color
- Once voted, the selected vote is locked — user cannot change it in the same session
- On vote: call submitFeedback(animeTitle, vote) from api/client.js
- Min touch target 44×44px on both buttons
- aria-label="Upvote {animeTitle}" and aria-label="Downvote {animeTitle}" for accessibility
```

---

### Prompt 22 — `animatch-frontend/src/components/DiscoveryGrid.jsx`

```
Create /animatch-frontend/src/components/DiscoveryGrid.jsx for AniMatch v2.0.

Requirements:
- Props: results (array), isLoading (boolean), error (string|null), pathway (string)
- Loading state: show a grid of 6 skeleton cards (pulsing grey placeholders matching card dimensions) — never a spinner alone
- Empty results (after search completes with 0 results): show centered message:
  "Nothing matched that description. Try different words or use the quiz to explore."
  With a "Try the quiz" button that calls onSwitchPathway("quiz") prop
- Error state: show the error message with a "Try again" button
- Results grid: responsive — 1 column mobile, 2 tablet (640px+), 3 desktop (1024px+)
- Gap between cards: lg (24px)
- Each result rendered as a card (build inline or import ResultCard):
  - Cover image (top, full width, aspect-ratio 2/3, object-fit cover) — on image error show a grey placeholder
  - Anime title: h3 style, ink color, 2 lines max then ellipsis
  - Genre tags: horizontal scrollable row of chips, body-sm, muted color, radius-sm, border
  - Synopsis excerpt: body-sm, muted, 3 lines max then ellipsis
  - FeedbackView component at the bottom
- Cards use radius-lg, shadow-card, surface-raised background
- Never nest a card inside a card
```

---

### Prompt 23 — `animatch-frontend/src/App.jsx`

```
Create /animatch-frontend/src/App.jsx — the main application shell for AniMatch v2.0.

Requirements:
- State managed here:
  - activePathway: "nlp" | "crossmedia" | "quiz" (default: "nlp")
  - results: array (default: [])
  - isLoading: boolean
  - error: string | null
  - crossMediaMatch: { title, year } | null (for the confirmation banner)

- Layout (top to bottom):
  1. Header: "AniMatch" wordmark left, tagline "Find your next favourite series" right — simple, no nav
  2. PathwayTabs — passes activePathway and onSelect handler
  3. Active panel (conditional render):
     - activePathway === "nlp" → NLPPanel
     - activePathway === "crossmedia" → CrossMediaPanel
     - activePathway === "quiz" → QuizModule
  4. DiscoveryGrid — always rendered below, shows results/loading/error states
  5. Footer: "AniMatch v2.0 · Semantic anime discovery" — minimal, muted

- When pathway changes: clear results, error, crossMediaMatch
- Max content width: 1200px, centered, horizontal padding 24px desktop / 16px mobile
- Sentence case on all text. No periods on labels or buttons.
- No React Router — single view SPA
```

---

### Prompt 24 — `animatch-frontend/src/main.jsx`

```
Update /animatch-frontend/src/main.jsx for AniMatch v2.0.

Requirements:
- Import React, ReactDOM, App, and /src/index.css
- Mount App to #root
- Wrap in React.StrictMode
- No other logic in this file
```

---

## PHASE 5 — DEPLOYMENT

### Prompt 25 — Vercel config (frontend)

```
Create /animatch-frontend/vercel.json for AniMatch v2.0 frontend deployment.

Requirements:
- Configure as SPA: all routes rewrite to /index.html so React handles routing client-side
- No serverless functions
- Also create /animatch-frontend/.env.example:
  VITE_API_BASE_URL=https://your-render-backend-url.onrender.com
  (with comment: "Get this from your Render dashboard after deploying the backend")
```

---

### Prompt 26 — Smoke test script

```
Create /animatch-backend/scripts/smoke_test.py — post-deployment verification script.

Requirements:
- Read BACKEND_URL from environment (e.g. https://animatch.onrender.com)
- Run 4 tests in sequence using httpx:
  1. GET /health → expect {"status": "ok"}
  2. POST /search/nlp with {"query": "dark psychological thriller with betrayal"} → expect results array length > 0, print first result title
  3. POST /search/crossmedia with {"title": "Interstellar"} → expect matched_title in response, print it
  4. POST /search/quiz with {pacing: "slow burn", tone: "dark and heavy", narrative_focus: "character growth", setting: "sci-fi / futuristic", stakes: "world-ending"} → expect results length > 0
  5. POST /feedback with {"anime_title": "Test Anime", "vote": "up"} → expect 200

- Print PASS / FAIL for each test with response time in ms
- Exit code 0 if all pass, exit code 1 if any fail
- Never use the requests library — httpx only (already in requirements.txt)
```

---

## QUICK REFERENCE — File → Prompt Map

| File | Prompt |
|---|---|
| app/config.py | 1 |
| app/inference.py | 2 |
| app/auth.py | 3 |
| app/qdrant_client.py | 4 |
| app/main.py | 5 |
| Run.sh | 6 |
| requirements.txt | 7 |
| routes/nlp.py | 8 |
| routes/crossmedia.py | 9 |
| routes/quiz.py | 10 |
| routes/feedback.py | 11 |
| routes/admin.py | 12 |
| scripts/export_onnx.py | 13 |
| scripts/vectorize_dataset.py | 14 |
| tailwind.config.js | 15 |
| src/api/client.js | 16 |
| src/components/PathwayTabs.jsx | 17 |
| NLPPanel.jsx | 18 |
| CrossMediaPanel.jsx | 19 |
| src/components/QuizModule.jsx | 20 |
| src/components/FeedbackView.jsx | 21 |
| src/components/DiscoveryGrid.jsx | 22 |
| src/App.jsx | 23 |
| src/main.jsx | 24 |
| vercel.json + .env.example | 25 |
| scripts/smoke_test.py | 26 |
