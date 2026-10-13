from datetime import datetime, timezone

from sqlmodel import Field, SQLModel


class UserBase(SQLModel):
    username: str = Field(index=True, unique=True, min_length=3, max_length=32)


class User(UserBase, table=True):
    __tablename__ = "users"

    id: int | None = Field(default=None, primary_key=True)
    password_hash: str = Field(nullable=False)  # never plaintext (R7.1)
    created_at: datetime = Field(
        default_factory=lambda: datetime.now(timezone.utc),
        nullable=False,
    )


class UserCreate(UserBase):
    password: str  # plaintext in, hashed before persist; never stored


class UserRead(UserBase):
    id: int  # NO password / password_hash field (R4.2)
