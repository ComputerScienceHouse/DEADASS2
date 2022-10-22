####################################
# File name: models.py             #
# Author: Joe Abbate               #
####################################
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import create_engine, Column, Integer, String, DateTime, \
     ForeignKey, event

Model = declarative_base(name='Model')

class Database(Model):
    __tablename__ = 'database'

    id = Column(Integer, primary_key=True, autoincrement=True)
    db_type = Column(String, nullable=False)
    name = Column(String, nullable=False)
    owner = Column(String, nullable=False)

    def __init__(self, db_type, name, owner):
        self.db_type = db_type
        self.name = name
        self.owner = owner

    def __repr__(self):
        return '<id {}>'.format(self.id)

    def get_id(self):
        return self.id