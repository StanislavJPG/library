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


class BookRating(BaseModel):
    __tablename__ = "rating"

    id: int
    url_orig: str
    title: str
    image: str
    description: str
    general_rating: float


class RatingService(BaseModel):
    current_book_url: str
    user_rating: conint(gt=0, le=5)
    title: str
