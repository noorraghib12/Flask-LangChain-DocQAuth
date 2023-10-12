from flask_login import UserMixin
from sqlalchemy.sql import func
from . import (db,
               load_conversation,
               VECTORSTORE_DIR)
class Queries(db.Model):
    id=db.Column(db.Integer,primary_key=True)
    query=db.Column(db.String(10000)) 
    answer=db.Column(db.String(10000))
    date=db.Column(db.DateTime(timezone=True),default=func.now())
    user_id=db.Column(db.Integer,db.ForeignKey('user.id'))




class User(db.Model,UserMixin):
    id=db.Column(db.Integer,primary_key=True)
    email=db.Column(db.String(150))
    password=db.Column(db.String(150))
    first_name=db.Column(db.String(150))
    queries=db.relationship('Queries')


# class Logged_in(db.Model):
#     user_id=db.Column(db.Integer,db.ForeignKey('user.id'))
#     date=db.Column(db.DateTime(timezone=True),default=datetime.now())
