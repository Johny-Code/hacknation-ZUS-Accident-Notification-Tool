from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routes import skan_router, form_router, voice_router

app = FastAPI(
    title="Work Accident Reporter API",
    description="API for reporting work accidents via scan, form, or voice",
    version="0.1.0"
)

# CORS middleware for frontend communication
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(skan_router)
app.include_router(form_router)
app.include_router(voice_router)


@app.get("/")
async def root():
    return {"status": "ok", "message": "Work Accident Reporter API"}


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
