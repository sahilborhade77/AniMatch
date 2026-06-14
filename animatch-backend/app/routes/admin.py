from collections import Counter
import httpx
from fastapi import APIRouter, Depends, HTTPException, status
from app.auth import require_admin
from app.config import settings

# Enforce require_admin dependency on all routes mounted under this router
router = APIRouter(
    prefix="/admin",
    tags=["admin"],
    dependencies=[Depends(require_admin)]
)

async def _fetch_raw_votes() -> list:
    """
    Helper function to query Supabase REST interface for all vote records.
    """
    headers = {
        "apikey": settings.SUPABASE_KEY,
        "Authorization": f"Bearer {settings.SUPABASE_KEY}"
    }
    
    supabase_url = f"{settings.SUPABASE_URL.rstrip('/')}/rest/v1/votes?select=*"
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                supabase_url,
                headers=headers,
                timeout=10.0
            )
            
        if response.status_code < 200 or response.status_code >= 300:
            print(f"Supabase GET votes failed with status {response.status_code}: {response.text}")
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail="Failed to retrieve vote telemetry from database."
            )
            
        return response.json()
        
    except HTTPException:
        raise
    except Exception as e:
        print(f"Exception during Supabase votes fetch: {e}")
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Failed to retrieve vote telemetry from database."
        )

@router.get("/votes")
async def get_votes():
    """
    Exposes the raw telemetry database records.
    """
    return await _fetch_raw_votes()

@router.get("/votes/summary")
async def get_votes_summary():
    """
    Computes aggregates on the vote telemetry.
    Returns total, upvotes, downvotes, and the top 10 most upvoted anime titles.
    """
    votes = await _fetch_raw_votes()
    
    total = len(votes)
    upvotes = sum(1 for v in votes if v.get("vote") == "up")
    downvotes = sum(1 for v in votes if v.get("vote") == "down")
    
    # Calculate top 10 upvoted anime titles using Counter
    upvoted_titles = [
        v.get("anime_title") for v in votes 
        if v.get("vote") == "up" and v.get("anime_title")
    ]
    title_counts = Counter(upvoted_titles)
    
    top_upvoted = [
        {"anime_title": title, "count": count}
        for title, count in title_counts.most_common(10)
    ]
    
    return {
        "total": total,
        "upvotes": upvotes,
        "downvotes": downvotes,
        "top_upvoted": top_upvoted
    }
