from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api import auth, complaints, analytics, predictions, priorities, hotspots

app = FastAPI(
    title="CivicPulse API",
    description="Urban infrastructure intelligence platform — complaints, analytics, "
                "predictions, and priority ranking.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # tighten before any real deployment
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(complaints.router)
app.include_router(analytics.router)
app.include_router(predictions.router)
app.include_router(priorities.router)
app.include_router(hotspots.router)


@app.get("/health")
def health():
    return {"status": "ok"}
