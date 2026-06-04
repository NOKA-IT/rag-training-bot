"""FastAPI application entrypoint."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from .database import init_db
from .init_admin import ensure_default_admin
from .routers import auth, users, departments, categories, documents, chat

app = FastAPI(title="RAG Training Bot API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
def on_startup():
    init_db()
    ensure_default_admin()


@app.get("/api/health")
def health():
    return {"status": "ok"}


app.include_router(auth.router)
app.include_router(users.router)
app.include_router(departments.router)
app.include_router(categories.router)
app.include_router(documents.router)
app.include_router(chat.router)
