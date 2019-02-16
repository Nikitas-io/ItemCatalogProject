from sqlalchemy import Column, ForeignKey, Integer, String, DateTime
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship
from sqlalchemy import create_engine

BASE = declarative_base()


class Users(BASE):
    __tablename__ = 'users'

    id = Column(Integer, primary_key=True)
    # Note that the name and e-mail should be unique.
    name = Column(String(80), nullable=False, unique=True)
    email = Column(String(100), nullable=False, unique=True)
    picture = Column(String(300))

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'email': self.email,
            'picture': self.picture,
        }


class Categories(BASE):
    __tablename__ = 'categories'

    id = Column(Integer, primary_key=True)
    # Note that the name has to be unique.
    name = Column(String(80), nullable=False, unique=True)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
        }


class CategoryItems(BASE):
    __tablename__ = 'category_items'

    id = Column(Integer, primary_key=True)
    # Note that the name has to be unique.
    name = Column(String(80), nullable=False)
    content = Column(String(250), nullable=False)
    category_id = Column(Integer, ForeignKey('categories.id'))
    category = relationship(Categories, cascade="all, delete-orphan")
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    user = relationship(Users, cascade="save-update")
    date_time = Column(DateTime, nullable=False)

    @property
    def serialize(self):
        """Return object data in easily serializeable format"""
        return {
            'id': self.id,
            'name': self.name,
            'content': self.content,
            'category_id': self.category_id,
            'user_id': self.user_id,
            # 'date_time': self.date_time
        }


ENGINE = create_engine(
    'postgresql+psycopg2://nikitas:nikitas@localhost/itemcatalog')

BASE.metadata.create_all(ENGINE)
