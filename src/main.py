import datetime
import os

from flask import Flask, render_template
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required

# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite://%s/app.db' % os.path.dirname(__file__)
app.config['SECURITY_REGISTERABLE'] = True
app.config['SECURITY_CHANGEABLE'] = True
app.config['SECURITY_SEND_REGISTER_EMAIL'] = False

# Create database connection object
db = SQLAlchemy(app)

def asdict(obj):
    return dict((col.name, getattr(obj, col.name))
                for col in class_mapper(obj.__class__).mapped_table.c)

# Define models
roles_users = db.Table('roles_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('role_id', db.Integer(), db.ForeignKey('role.id')))

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    confirmed_at = db.Column(db.DateTime())
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))

transactions_users = db.Table('transactions_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('transaction_id', db.Integer(), db.ForeignKey('transaction.id')))

class Transaction(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(1024))
    vendor = db.Column(db.String(255))
    amount_cents = db.Column(db.Integer)
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship("User", backref = "created_transactions")
    participants = db.relationship("User", secondary = transactions_users,
                                   backref = "transactions")
    created = db.Column(db.DateTime, default = datetime.datetime.now)
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'))
    event = db.relationship("Event", backref = "transactions")

events_users = db.Table('events_users',
        db.Column('user_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('event_id', db.Integer(), db.ForeignKey('event.id')))

class Event(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(255))
    description = db.Column(db.String(1024))
    creator_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    creator = db.relationship("User", backref = "created_events")
    participants = db.relationship("User", secondary = events_users,
                                   backref = "events")
    created = db.Column(db.DateTime, default = datetime.datetime.now)

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Api stuff
@app.route('/api/user/<int:userid>', methods = ['GET'])
def get_user_data(userid):
    pass

# Views
@app.route('/')
@login_required
def home():
    return "Hello World!"

if __name__ == '__main__':
    app.run()
