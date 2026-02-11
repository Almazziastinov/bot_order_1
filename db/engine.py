from sqlalchemy import create_engine
from db.models import Base

engine = create_engine('sqlite:///db.sqlite3')

def create_db():
    Base.metadata.create_all(engine)
