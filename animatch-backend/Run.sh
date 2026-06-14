#!/bin/bash

# WARNING & CRITICAL CONSTRAINT:
# We must use exactly ONE worker (--workers 1).
# Multiple uvicorn worker processes would each load a separate copy of the ONNX model
# into memory, which would instantly exceed the Render free-tier 120MB memory budget.

# Activate virtual environment if it exists locally or on Render
if [ -d ".venv" ]; then
    source .venv/bin/activate
elif [ -d "venv" ]; then
    source venv/bin/activate
fi

# Run FastAPI app via uvicorn with a single worker
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000} --workers 1
