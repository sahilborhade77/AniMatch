from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from fastapi.concurrency import run_in_threadpool
from app.inference import encode
from app.qdrant_client import search_vectors

router = APIRouter(prefix="/search/quiz", tags=["quiz"])

class QuizRequest(BaseModel):
    pacing: str = Field(..., min_length=2)
    tone: str = Field(..., min_length=2)
    narrative_focus: str = Field(..., min_length=2)
    setting: str = Field(..., min_length=2)
    stakes: str = Field(..., min_length=2)

    # Forbid any extra fields in the payload to ensure exactly 5 fields
    model_config = {
        "extra": "forbid"
    }

@router.post("/", include_in_schema=False)
@router.post("")
async def search_quiz(payload: QuizRequest):
    """
    Accepts 5 structured parameters from the quiz, synthesizes them into
    a descriptive paragraph, enriches it, and queries Qdrant to return recommendations.
    """
    # 1. Synthesize the 5 fields into a single descriptive paragraph
    synthesized_paragraph = (
        f"A {payload.pacing} series with a {payload.tone} tone, "
        f"focused on {payload.narrative_focus}, set in a {payload.setting} world, "
        f"with {payload.stakes} at stake."
    )
    
    try:
        # 2. Prepend feature enrichment template using synthesized paragraph
        enriched_query = f"Title: . Genres: . Studio: . Synopsis: {synthesized_paragraph}"
        
        # Run blocking/cpu-bound encode() in a threadpool to keep the event loop non-blocking
        vector = await run_in_threadpool(encode, enriched_query)
        
        # Query remote Qdrant Cloud cluster
        results = await search_vectors(vector)
        
        return {
            "synthesized_prompt": synthesized_paragraph,
            "results": results
        }
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Quiz Search execution failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search is temporarily unavailable. Try again shortly."
        )
