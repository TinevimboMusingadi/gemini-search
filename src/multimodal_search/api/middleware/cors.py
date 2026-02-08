"""CORS middleware for FastAPI."""
from fastapi import FastAPI
from starlette.middleware.cors import CORSMiddleware


def add_cors(app: FastAPI, allow_origins: list[str] | None = None) -> None:
    if allow_origins is None:
        allow_origins = ["*"]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allow_origins,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
