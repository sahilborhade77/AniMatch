from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from app.inference import encode
from app.qdrant_client import search_vectors

router = APIRouter(prefix="/search/nlp", tags=["nlp"])

class NLPRequest(BaseModel):
    query: str = Field(..., min_length=3, max_length=1000)

@router.post("/", include_in_schema=False)
@router.post("")
async def search_nlp(payload: NLPRequest):
    """
    Accepts natural language query, applies feature enrichment template,
    vectorizes it using the ONNX model, and queries Qdrant to return recommendations.
    """
    try:
        # Prepend feature enrichment template to query to align vector space with indexed records
        enriched_query = f"Title: . Genres: . Studio: . Synopsis: {payload.query}"
        
        # Run blocking/cpu-bound encode() in a threadpool to keep the event loop non-blocking
        vector = await run_in_threadpool(encode, enriched_query)
        
        # Query remote Qdrant Cloud cluster
        results = await search_vectors(vector)
        
        return {"results": results}
        
    except HTTPException:
        # Re-raise known HTTPExceptions (e.g., 503 from qdrant_client)
        raise
    except Exception as e:
        # Log generic exceptions locally and return HTTP 503
        print(f"NLP Search execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search is temporarily unavailable. Try again shortly."
        )
