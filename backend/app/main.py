from contextlib import asynccontextmanager

from fastapi import Depends, FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from sqlmodel import Session, select

from app.core.config import get_settings
from app.db.session import get_session
from app.models.item import Item, ItemCreate, ItemRead
from app.routers import auth, papers

settings = get_settings()


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Schema is managed by Alembic migrations, applied by the container
    # entrypoint (alembic upgrade head) before the server starts. Nothing
    # to do here at startup.
    yield


app = FastAPI(title="muit-hackathon API", version="0.1.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


app.include_router(papers.router)


@app.get("/health", tags=["meta"])
def health() -> dict[str, str]:
    return {"status": "ok"}


app.include_router(auth.router)


@app.get("/api/items", response_model=list[ItemRead], tags=["items"])
def list_items(session: Session = Depends(get_session)) -> list[Item]:
    return list(session.exec(select(Item).order_by(Item.id)).all())


@app.post("/api/items", response_model=ItemRead, status_code=201, tags=["items"])
def create_item(payload: ItemCreate, session: Session = Depends(get_session)) -> Item:
    item = Item.model_validate(payload)
    session.add(item)
    session.commit()
    session.refresh(item)
    return item


@app.get("/api/items/{item_id}", response_model=ItemRead, tags=["items"])
def get_item(item_id: int, session: Session = Depends(get_session)) -> Item:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    return item


@app.delete("/api/items/{item_id}", status_code=204, tags=["items"])
def delete_item(item_id: int, session: Session = Depends(get_session)) -> None:
    item = session.get(Item, item_id)
    if item is None:
        raise HTTPException(status_code=404, detail="Item not found")
    session.delete(item)
    session.commit()
