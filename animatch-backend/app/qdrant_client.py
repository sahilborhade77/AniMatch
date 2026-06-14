import csv
import io
import os
import zipfile

from fastapi import HTTPException, status
from fastapi.concurrency import run_in_threadpool
from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings

# Initialize QdrantClient with in-memory mode for local testing or remote URL for production
if settings.QDRANT_URL == ":memory:":
    # In-memory mode for local testing
    client = QdrantClient(":memory:")
    # Create collection if it doesn't exist (for testing)
    try:
        client.create_collection(
            collection_name=settings.COLLECTION_NAME,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE),
        )
    except:
        pass  # Collection might already exist
else:
    # Remote Qdrant Cloud
    client = QdrantClient(
        url=settings.QDRANT_URL,
        api_key=settings.QDRANT_API_KEY
    )


def _load_local_anime_records(limit: int = 1000) -> list[dict]:
    dataset_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "..", "..", "data set")
    )
    mal_zip_path = os.path.join(dataset_dir, "MyAnimeList Dataset.zip")
    analytics_zip_path = os.path.join(dataset_dir, "Anime & Manga Analytics Dataset (2026).zip")

    metadata_map = {}
    if os.path.exists(analytics_zip_path):
        with zipfile.ZipFile(analytics_zip_path) as z:
            with z.open("anime_dataset.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
                for row in reader:
                    mal_id = row.get("mal_id")
                    if mal_id:
                        metadata_map[mal_id] = {
                            "genres": (row.get("genres") or "").replace("|", ", "),
                            "studio": row.get("studios") or "",
                        }

    if not os.path.exists(mal_zip_path):
        raise FileNotFoundError(f"MyAnimeList Dataset zip not found at {mal_zip_path}")

    records = []
    with zipfile.ZipFile(mal_zip_path) as z:
        with z.open("anime.csv") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding="utf-8"))
            for row in reader:
                anime_id = row.get("anime_id")
                meta = metadata_map.get(anime_id, {"genres": "", "studio": ""})
                records.append({
                    "anime_id": anime_id,
                    "title": row.get("title", ""),
                    "genres": meta["genres"],
                    "studio": meta["studio"],
                    "synopsis": row.get("synopsis", ""),
                    "cover_image_url": row.get("image_url", ""),
                })
                if len(records) >= limit:
                    break

    return records


def seed_in_memory_collection(limit: int = 1000) -> None:
    """
    Populate the API's in-process Qdrant instance for local demos/tests.
    Remote Qdrant deployments should be populated with scripts/vectorize_dataset.py.
    """
    if settings.QDRANT_URL != ":memory:":
        return

    existing = client.count(collection_name=settings.COLLECTION_NAME, exact=True).count
    if existing:
        return

    from app.inference import encode

    points = []
    for index, rec in enumerate(_load_local_anime_records(limit=limit)):
        enriched_text = (
            f"Title: {rec['title']}. Genres: {rec['genres']}. "
            f"Studio: {rec['studio']}. Synopsis: {rec['synopsis']}"
        )
        try:
            point_id = int(rec["anime_id"])
        except (TypeError, ValueError):
            point_id = index

        points.append(PointStruct(
            id=point_id,
            vector=encode(enriched_text),
            payload={
                "title": rec["title"],
                "genres": rec["genres"],
                "studio": rec["studio"],
                "synopsis": rec["synopsis"],
                "cover_image_url": rec["cover_image_url"] or "",
            },
        ))

        if len(points) == 100:
            client.upsert(collection_name=settings.COLLECTION_NAME, points=points)
            points = []

    if points:
        client.upsert(collection_name=settings.COLLECTION_NAME, points=points)

def _search_vectors_sync(vector: list[float], top_k: int = 10) -> list[dict]:
    """
    Synchronous search function that queries Qdrant.
    """
    try:
        response = client.search(
            collection_name=settings.COLLECTION_NAME,
            query_vector=vector,
            limit=top_k
        )
        
        results = []
        for point in response:
            payload = point.payload or {}
            results.append({
                "title": payload.get("title", ""),
                "genres": payload.get("genres", ""),
                "studio": payload.get("studio", ""),
                "synopsis": payload.get("synopsis", ""),
                "cover_image_url": payload.get("cover_image_url", ""),
                "score": float(point.score)
            })
            
        return results

    except Exception as e:
        # Log the actual exception locally
        print(f"Qdrant connection/query failure: {e}")
        # Raise HTTP 503 service unavailable as requested
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail="Search service unavailable. Try again shortly."
        )

async def search_vectors(vector: list[float], top_k: int = 10) -> list[dict]:
    """
    Async wrapper for search_vectors - runs the sync function in a threadpool.
    """
    return await run_in_threadpool(_search_vectors_sync, vector, top_k)
