"""Z-FORGE FastAPI application (minimal — full implementation in T7)."""

from fastapi import FastAPI

app = FastAPI(
    title="Z-FORGE API",
    description="AI Change Engineering platform for IBM Z artifacts",
    version="0.1.0",
)


@app.get("/health")
async def health() -> dict[str, str]:
    return {"status": "ok", "service": "zforge-api"}
