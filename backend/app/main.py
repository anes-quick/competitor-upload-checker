from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router

try:
  from dotenv import load_dotenv
  load_dotenv()
except Exception:
  # If python-dotenv isn't installed, we just rely on real env vars (Railway, shell, etc.)
  pass


def create_app() -> FastAPI:
  """
  Application factory to create the FastAPI app.

  This makes it easier to configure the app differently for tests,
  local development, and production.
  """
  app = FastAPI(
    title="Competitor Upload Checker Backend",
    version="0.1.0",
  )

  app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:8000", "http://127.0.0.1:8000"],
    allow_origin_regex=r"https://.*\.vercel\.app",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  app.include_router(api_router, prefix="/api")

  return app


app = create_app()

