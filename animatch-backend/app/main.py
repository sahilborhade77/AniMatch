import logging
from fastapi import FastAPI, Request, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from app.config import settings

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("animatch")

# Instantiate FastAPI application
app = FastAPI(
    title="AniMatch API",
    version="2.0"
)

# CORS middleware origin locking
app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.FRONTEND_URL],
    allow_credentials=True,
    allow_methods=["POST", "GET"],
    allow_headers=["Authorization", "Content-Type"],
)

# Mount individual routers
from app.routes import nlp, crossmedia, quiz, feedback, admin

app.include_router(nlp.router)
app.include_router(crossmedia.router)
app.include_router(quiz.router)
app.include_router(feedback.router)
app.include_router(admin.router)

# GET /health - Render health checks and deployment status
@app.get("/health", status_code=status.HTTP_200_OK)
def health_check():
    return {"status": "ok", "version": "2.0"}

# Global exception handler - catches unhandled exceptions and processes HTTPExceptions gracefully
from starlette.exceptions import HTTPException as StarletteHTTPException

@app.exception_handler(Exception)
async def global_exception_handler(request: Request, exc: Exception):
    if isinstance(exc, StarletteHTTPException):
        content = exc.detail if isinstance(exc.detail, dict) else {"error": exc.detail}
        return JSONResponse(
            status_code=exc.status_code,
            content=content
        )
    logger.error(f"Unhandled system exception: {exc}", exc_info=True)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"error": "An unexpected error occurred. Please try again."}
    )


# Startup event logging
@app.on_event("startup")
async def startup_event():
    # Import inside to make sure modules load successfully and dependencies are ready
    from app.inference import session
    from app.qdrant_client import client, seed_in_memory_collection
    from fastapi.concurrency import run_in_threadpool

    await run_in_threadpool(seed_in_memory_collection)
    
    logger.info("ONNX model loaded and inference session ready.")
    logger.info("Qdrant client initialized successfully.")
