import os
import sys
import time
import zipfile
import csv
import io

# Setup python path to import app modules correctly
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from qdrant_client import QdrantClient
from qdrant_client.models import Distance, VectorParams, PointStruct
from app.config import settings
from app.inference import encode

def main():
    start_time = time.time()
    
    # Setup dataset paths
    dataset_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "data set"))
    mal_zip_path = os.path.join(dataset_dir, "MyAnimeList Dataset.zip")
    analytics_zip_path = os.path.join(dataset_dir, "Anime & Manga Analytics Dataset (2026).zip")
    
    # 1. Build genres and studios lookup mapping from Analytics dataset to enrich MyAnimeList Dataset
    print("Building genres and studios metadata mapping from Analytics dataset...")
    metadata_map = {}
    if os.path.exists(analytics_zip_path):
        with zipfile.ZipFile(analytics_zip_path) as z:
            with z.open("anime_dataset.csv") as f:
                reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
                for row in reader:
                    mal_id = row.get("mal_id")
                    if mal_id:
                        # Clean up genres: replace '|' with ', ' for better vector space syntax
                        raw_genres = row.get("genres", "")
                        genres = raw_genres.replace("|", ", ") if raw_genres else ""
                        studio = row.get("studios", "")
                        metadata_map[mal_id] = {
                            "genres": genres,
                            "studio": studio
                        }
    else:
        print(f"Warning: Analytics dataset zip not found at {analytics_zip_path}")

    # 2. Read MyAnimeList Dataset (primary source)
    print("Reading MyAnimeList Dataset...")
    records = []
    if not os.path.exists(mal_zip_path):
        raise FileNotFoundError(f"MyAnimeList Dataset zip not found at {mal_zip_path}")
        
    with zipfile.ZipFile(mal_zip_path) as z:
        with z.open("anime.csv") as f:
            reader = csv.DictReader(io.TextIOWrapper(f, encoding='utf-8'))
            for row in reader:
                anime_id = row.get("anime_id")
                title = row.get("title", "")
                synopsis = row.get("synopsis", "")
                cover_image_url = row.get("image_url", "")
                
                # Fetch genres and studio from metadata map
                meta = metadata_map.get(anime_id, {"genres": "", "studio": ""})
                genres = meta["genres"]
                studio = meta["studio"]
                
                records.append({
                    "anime_id": anime_id,
                    "title": title,
                    "genres": genres,
                    "studio": studio,
                    "synopsis": synopsis,
                    "cover_image_url": cover_image_url
                })
                
    total_records = len(records)
    print(f"Loaded {total_records} records from MyAnimeList dataset.")

    # 3. Initialize Qdrant Client and configure collection
    print("Connecting to Qdrant Cloud...")
    qdrant_client = QdrantClient(url=settings.QDRANT_URL, api_key=settings.QDRANT_API_KEY)
    
    collection_name = settings.COLLECTION_NAME
    if not qdrant_client.collection_exists(collection_name):
        print(f"Creating Qdrant collection '{collection_name}'...")
        qdrant_client.create_collection(
            collection_name=collection_name,
            vectors_config=VectorParams(size=384, distance=Distance.COSINE)
        )
    else:
        print(f"Qdrant collection '{collection_name}' already exists.")

    # 4. Process and upload records in batches of 100
    print("Starting vectorization and uploading in batches of 100...")
    points = []
    uploaded_count = 0
    
    for i, rec in enumerate(records):
        title = rec["title"]
        genres = rec["genres"]
        studio = rec["studio"]
        synopsis = rec["synopsis"]
        cover_image_url = rec["cover_image_url"] if rec["cover_image_url"] else ""
        
        # Apply feature enrichment formula
        enriched_text = f"Title: {title}. Genres: {genres}. Studio: {studio}. Synopsis: {synopsis}"
        
        try:
            # Encode enriched string using inference.py encode()
            vector = encode(enriched_text)
            
            # Map point ID
            try:
                point_id = int(rec["anime_id"])
            except (ValueError, TypeError):
                point_id = i
                
            point = PointStruct(
                id=point_id,
                vector=vector,
                payload={
                    "title": title,
                    "genres": genres,
                    "studio": studio,
                    "synopsis": synopsis,
                    "cover_image_url": cover_image_url
                }
            )
            points.append(point)
            
        except Exception as e:
            print(f"Skipping record index {i} ('{title}') due to encoding/processing failure: {e}")
            continue
            
        # Push to Qdrant on batch size 100 or when reaching end of list
        if len(points) == 100 or i == total_records - 1:
            qdrant_client.upsert(
                collection_name=collection_name,
                points=points
            )
            uploaded_count += len(points)
            points = []
            
            # Print progress every 500 records
            if uploaded_count % 500 == 0 or uploaded_count == total_records:
                print(f"Uploaded {uploaded_count}/{total_records}...")
                
    end_time = time.time()
    elapsed_time = end_time - start_time
    print(f"Vectorization and upload completed successfully in {elapsed_time:.2f} seconds.")

if __name__ == "__main__":
    main()
