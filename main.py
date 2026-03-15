from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from routes.chat import router as chat_router
from routes.projects import router as projects_router

app = FastAPI(
    title="Project Agent API",
    description="AI agent for querying and updating projects",
    version="1.0.0"
)

# Allow frontend (React) to call this API
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],   # lock this down in production
    allow_methods=["*"],
    allow_headers=["*"],
)

# Register routes
app.include_router(chat_router,     prefix="/api", tags=["Agent"])
app.include_router(projects_router, prefix="/api", tags=["Projects"])

@app.get("/")
def root():
    return {"status": "running", "docs": "/docs"}