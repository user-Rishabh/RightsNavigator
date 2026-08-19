from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv
from app.database import init_db
from app.routers.api import router as api_router

load_dotenv()

app = FastAPI(
    title="RightsNavigator AI Backend",
    description="AI Engine for Citizen Civic & Legal Empowerment - OOSC 4.0 Hackathon",
    version="1.0.0"
)

# Enable CORS for frontend development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def startup_event():
    init_db()
    print("🚀 SQLite Rights Navigator Database & Knowledge Engine Initialized!")

app.include_router(api_router)

@app.get("/")
def root():
    return {
        "message": "Welcome to RightsNavigator AI Backend",
        "track": "PS3 — AI for Civic and Legal Empowerment",
        "docs": "/docs"
    }
