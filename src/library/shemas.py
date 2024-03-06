import uuid
from typing import Optional

from pydantic import BaseModel, conint


class BookCreate(BaseModel):
    __tablename__ = "book"

    id: Optional[int] = None
    title: str
    image: Optional[str] = None
    description: Optional[str] = None
    url: Optional[str] = None
    url_orig: Optional[str] = None


class BookAndRatingRead(BookCreate):
    rating: conint(gt=0, le=5)


class Library(BaseModel):
    __tablename__ = "library"

    id: int
    user_id: uuid.UUID
    book_id: int
    rating: int
    is_saved_to_profile: bool


class RatingService(BaseModel):
    current_book_url: str
    user_rating: conint(gt=0, le=5)
    title: str
    num: int
