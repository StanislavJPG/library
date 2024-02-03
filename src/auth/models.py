from uuid import uuid4
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy import Column, String, Boolean
from sqlalchemy.orm import relationship

from src.database import Base


class User(Base):
    __tablename__ = "user"
    __table_args__ = {'extend_existing': True}

    id = Column(UUID, primary_key=True, unique=True, index=True, nullable=False, default=uuid4)
    email = Column(String, unique=True, index=True, nullable=False)
    username = Column(String)
    hashed_password = Column(String)
    is_active = Column(Boolean, default=True)
    profile_image = Column(String)

    libraries = relationship("Library", back_populates="user")
