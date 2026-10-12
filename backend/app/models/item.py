from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class ItemBase(SQLModel):
    name: str = Field(index=True, min_length=1, max_length=255)
    description: str | None = Field(default=None, max_length=1024)


class Item(ItemBase, table=True):
    __tablename__ = "items"

    id: int | None = Field(default=None, primary_key=True)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class ItemCreate(ItemBase):
    pass


class ItemRead(ItemBase):
    id: int
    created_at: datetime
