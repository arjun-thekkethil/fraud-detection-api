from fastapi.middleware.cors import CORSMiddleware
from main import app as main_app  # Import the real app with routes

# CORS middleware setup
main_app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app = main_app  # This is the ASGI app for Uvicorn
