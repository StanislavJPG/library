import uuid

from pydantic import BaseModel


class BookCreate(BaseModel):
    __tablename__ = "book"

    id: uuid.UUID
    title: str
    description: str
    owner_id: int