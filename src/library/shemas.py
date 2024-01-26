import uuid

from pydantic import BaseModel, conint


class BookCreate(BaseModel):
    __tablename__ = "book"

    id: uuid.UUID
    title: str
    description: str
    url: str
    url_orig: str
    owner_id: int
    user_rating: int
    general_ratings: int


class RatingService(BaseModel):
    current_book_url: str
    user_rating: conint(gt=0, le=5)
