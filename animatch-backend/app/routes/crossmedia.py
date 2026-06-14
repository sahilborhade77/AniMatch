import json
import os
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from app.inference import encode
from app.qdrant_client import search_vectors

# Load baseline index once at module level
DATA_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data"))
IMDB_INDEX_PATH = os.path.join(DATA_DIR, "imdb_index.json")

if not os.path.exists(IMDB_INDEX_PATH):
    raise FileNotFoundError(f"IMDb baseline index not found at {IMDB_INDEX_PATH}")

with open(IMDB_INDEX_PATH, "r", encoding="utf-8") as f:
    imdb_index = json.load(f)

router = APIRouter(prefix="/search/crossmedia", tags=["crossmedia"])

class CrossMediaRequest(BaseModel):
    title: str = Field(..., min_length=3, max_length=1000)

def find_imdb_match(query_title: str) -> dict | None:
    """
    Fuzzy matches the submitted title against the local index (case-insensitive, partial match acceptable).
    """
    query = query_title.lower().strip()
    
    # 1. Look for exact title match
    for entry in imdb_index:
        if entry["title"].lower().strip() == query:
            return entry
            
    # 2. Look for partial substring match (query is part of the title)
    for entry in imdb_index:
        if query in entry["title"].lower():
            return entry
            
    # 3. Look for partial substring match (title is part of the query)
    for entry in imdb_index:
        if entry["title"].lower() in query:
            return entry
            
    return None

@router.post("/", include_in_schema=False)
@router.post("")
async def search_crossmedia(payload: CrossMediaRequest):
    """
    Fuzzy-matches a mainstream movie/TV show against the local index,
    extracts its synopsis, enriches it, and runs a semantic search to return recommendations.
    """
    # Attempt to find match in local index
    match = find_imdb_match(payload.title)
    
    if not match:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="We couldn't find that title in our index. Try a different movie or show name."
        )
        
    matched_title = match["title"]
    matched_year = match["year"]
    synopsis = match["synopsis"]
    
    try:
        # Prepend feature enrichment template using the matched title and synopsis
        enriched_query = f"Title: {matched_title}. Genres: . Studio: . Synopsis: {synopsis}"
        
        # Run synchronous encode() in a threadpool to keep the event loop non-blocking
        vector = await run_in_threadpool(encode, enriched_query)
        
        # Query remote Qdrant Cloud cluster
        results = await search_vectors(vector)
        
        return {
            "matched_title": matched_title,
            "matched_year": matched_year,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Crossmedia Search execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search is temporarily unavailable. Try again shortly."
        )
