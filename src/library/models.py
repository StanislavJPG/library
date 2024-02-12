from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, Integer, String, ForeignKey, Boolean, Float
from sqlalchemy.orm import relationship

from src.auth.models import User
from src.database import Base


class Book(Base):
    __tablename__ = "book"

    id = Column(Integer, primary_key=True, unique=True, index=True)
    title = Column(String)
    image = Column(String)
    description = Column(String)
    url = Column(String)
    url_orig = Column(String)

    libraries = relationship("Library", back_populates="book")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}


class Library(Base):
    __tablename__ = "library"

    # this is an association table, that takes id's from Book and User models as foreign keys

    user_id = Column(UUID(as_uuid=True), ForeignKey(User.id), primary_key=True)
    book_id = Column(Integer, ForeignKey(Book.id), primary_key=True)
    rating = Column(Integer)
    is_saved_to_profile = Column(Boolean)

    book = relationship("Book", back_populates="libraries")
    user = relationship(User, back_populates="libraries")

    def as_dict(self):
        return {c.name: getattr(self, c.name) for c in self.__table__.columns}
