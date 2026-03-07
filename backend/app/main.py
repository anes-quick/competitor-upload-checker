from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .api import router as api_router


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
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
  )

  app.include_router(api_router, prefix="/api")

  return app


app = create_app()

