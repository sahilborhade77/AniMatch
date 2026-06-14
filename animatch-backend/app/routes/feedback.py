from datetime import datetime
from typing import Literal
import httpx
from fastapi import APIRouter, HTTPException, status
from pydantic import BaseModel, Field
from app.config import settings

router = APIRouter(prefix="/feedback", tags=["feedback"])

class FeedbackRequest(BaseModel):
    anime_title: str = Field(..., min_length=1, max_length=500)
    vote: Literal["up", "down"]

@router.post("/", include_in_schema=False)
@router.post("")
async def record_feedback(payload: FeedbackRequest):
    """
    Public endpoint that records user upvotes/downvotes.
    Pushes telemetry directly to Supabase via its REST interface.
    """
    # 1. Build payload containing ISO timestamp
    iso_timestamp = datetime.utcnow().isoformat()
    supabase_payload = {
        "anime_title": payload.anime_title,
        "vote": payload.vote,
        "created_at": iso_timestamp
    }
    
    # 2. Build headers required for Supabase REST API
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal"
    }
    
    supabase_url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/votes"
    
    try:
        # Use httpx.AsyncClient for non-blocking HTTP communications
        async with httpx.AsyncClient() as client:
            response = await client.post(
                supabase_url,
                json=supabase_payload,
                headers=headers,
                timeout=10.0
            )
            
        # Check if Supabase returned a successful 2xx response
        if response.status_code < 200 or response.status_code >= 300:
            print(f"Supabase feedback persistence failed with status {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="We couldn't save your feedback right now."
            )
            
        return {"message": "Feedback recorded."}
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception during Supabase communication: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="We couldn't save your feedback right now."
        )
