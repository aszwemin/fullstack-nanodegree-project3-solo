from datetime import datetime

from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

Base = declarative_base()


class User(Base):

    __tablename__ = 'user'

    id = Column(Integer, primary_key=True)
    name = Column(String(80), nullable=False)
    email = Column(String(80), nullable=False)
    picture = Column(String(80))


class Genre(Base):

    __tablename__ = 'genre'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)


class Movie(Base):

    __tablename__ = 'movie'

    name = Column(String(80), nullable=False)
    id = Column(Integer, primary_key=True)
    year = Column(String(250))
    description = Column(String(250))
    director = Column(String(8))
    genre_id = Column(Integer, ForeignKey('genre.id'))
    user_id = Column(Integer, ForeignKey('user.id'))
    created_date = Column(DateTime, default=datetime.now())
    genre = relationship(Genre)
    user = relationship(User)

    @property
    def serialize(self):
        return {
            "name": self.name,
            "description": self.description,
            "id": self.id,
            "year": self.year,
            "director": self.director
        }

engine = create_engine('sqlite:///moviescatalog.db')
Base.metadata.create_all(engine)
