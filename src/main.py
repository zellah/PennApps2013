import datetime
import os
import json

from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from sqlalchemy.orm import class_mapper

dthandler = lambda obj: obj.isoformat() if isinstance(obj, datetime.datetime) else None
# Create app
app = Flask(__name__)
app.config['DEBUG'] = True
app.config['SECRET_KEY'] = 'super-secret'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///%s/app.db' % (os.path.abspath(os.path.dirname(__file__)),)
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

friends = db.Table('friends',
        db.Column('f1_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('f2_id', db.Integer(), db.ForeignKey('user.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    names = db.Column(db.String(255))
    password = db.Column(db.String(255))
    active = db.Column(db.Boolean())
    created = db.Column(db.DateTime(), default = datetime.datetime.now)
    roles = db.relationship('Role', secondary=roles_users,
                            backref=db.backref('users', lazy='dynamic'))
    friends = db.relationship('User', secondary=friends,
                            primaryjoin=friends.c.f1_id==id, secondaryjoin=friends.c.f2_id==id)
    venmo_key = db.Column(db.String(255))

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
    event_id = db.Column(db.Integer, db.ForeignKey('event.id'), nullable=True)
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
    settled = db.Column(db.Boolean)
    end_date = db.Column(db.DateTime, default = lambda: datetime.datetime.now()
            + datetime.timedelta(days=2))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore)

# Api stuff
@app.route('/api/user/<int:userid>', methods = ['GET'])
def display_user_data(userid):
    return json.dumps(get_user_data(userid), default=dthandler)

def get_user_data(userid):
    user = User.query.filter(User.id==userid).first()
    if not user:
        return 'user not found', 404
    userdict = asdict(user)
    del userdict['password']
    userdict['friends'] = get_friends(userid)
    return userdict

@app.route('/api/user/<int:userid>/friends', methods = ['GET'])
def display_friend_data(userid):
    friends = [get_user_data(friend_id) for friend_id in get_friends(userid)]
    return json.dumps(get_friends(friends), default=dthandler)

def get_friends(userid):
    return [row.f2_id for row in db.session.query(friends.c.f1_id == userid).all()]

@app.route('/api/transaction/<int:transid>', methods = ['GET'])
def display_transaction_data(transid):
    transaction_dict = get_transaction_dict(transid)
    return json.dumps(transaction_dict, default=dthandler)

def get_transaction_data(transid):
    transaction = Transaction.query.filter(Transaction.id == transid).first()
    if not transaction:
        return 'transaction not found', 404
    transaction_dict = asdict(transaction)
    transaction_dict['creator'] = asdict(transaction.creator)
    transaction_dict['participants'] = [asdict(participant)
            for participant in transaction.participants]
    return transaction_dict

@app.route('/api/event/<int:eventid>', methods = ['GET'])
def display_event_data(eventid):
    event = Event.query.filter(Event.id == eventid).first()
    if not event:
        return 'event not found', 404
    event_dict = asdict(event)
    event_dict['transactions'] = [get_transaction_data(transaction.id)
            for transaction in event.transactions]
    event_dict['participants'] = [asdict(participant)
            for participant in event.participants]
    event_dict['creator'] = asdict(event.creator)
    return json.dumps(event_dict, default=dthandler)

@app.route('/api/event/<int:eventid>/transactions', methods = ['GET'])
def display_transactions(eventid):
    event = Event.query.filter(Event.id == eventid).first()
    if not event:
        return 'event not found', 404
    return json.dumps(map(asdict, event.transactions), default=dthandler)

@app.route('/api/transaction', methods = ['POST'])
@login_required
def new_transaction():
    modified_form = request.form.copy()
    participant_ids = []
    if 'participants' in modified_form:
        participant_ids = modified_form['participants']
        del modified_form['participants']
    modified_form['creator_id'] = current_user.id
    transaction = Transaction(**modified_form)
    db.session.add(transaction)
    db.session.commit()
    for participant_id in participant_ids:
        conn = db.session.connection()
        conn.execute(transactions_users.insert(
            transaction_id=transaction.id, user_id=participant_id))
        conn.close()

@app.route('/api/event', methods = ['POST'])
@login_required
def new_event():
    modified_form = request.form.copy()
    participant_ids = []
    if 'participants' in modified_form:
        participant_ids = modified_form['participants']
        del modified_form['participants']
    transaction_ids = []
    if 'transactions' in modified_form:
        transaction_ids = modified_form['transactions']
        del modified_form['transactions']
    modified_form['creator_id'] = current_user.id
    event = Event(**modified_form)
    db.session.add(event)
    db.session.commit()
    for participant_id in participant_ids:
        conn = db.session.connection()
        conn.execute(events_users.insert(
            event_id=event.id, user_id=participant_id))
        conn.close()
    for transaction_id in transaction_ids:
        transaction = Transaction.query.filter(Transaction.id == transaction_id).one()
        transaction.event = event
        db.session.add(transaction)
    db.session.commit()

@app.route('/api/user', methods = ['POST'])
def new_user():
    raise NotImplemented

@app.route('/api/transaction/<int:transid>', methods= ['POST'])
def edit_transaction(transid):
    trans_to_edit = Transaction.query.filter(Transaction.id == transid).first()
    if not trans_to_edit:
        return 'no such transaction', 404
    for k,v in request.form.items():
        if k == 'creator' or k == 'creator_id':
            trans_to_edit.creator_id = v
        elif k == 'event' or k == 'event_id':
            trans_to_edit.event_id = v
        elif k == 'new_participants':
            for participant_id in v:
                trans_to_edit.participants.append(
                    User.query.filter(User.id == participant_id).one())
        elif k == 'all_participants':
            del trans_to_edit.participants[:]
            for participant_id in v:
                trans_to_edit.participants.append(User.query.filter(User.id == participant_id).one())
        elif k == 'del_participants':
            conn = db.session.connection()
            conn.execute(transactions_users.delete().where(
                transactions_users.c.user_id.in_(v)).where(
                transactions_users.c.transaction_id == trans_to_edit.id))
            conn.close()
        else:
            setattr(trans_to_edit, k, v)
    db.session.add(trans_to_edit)
    db.session.commit()

@app.route('/api/event/<int:eventid>', methods=['POST'])
def edit_event(eventid):
    event_to_edit = Event.query.filter(Event.id == eventid).first()
    if not event_to_edit:
        return 'no such event', 404
    for k,v in request.form.items():
        if k == 'creator' or k == 'creator_id':
            event_to_edit.creator_id = v
        elif k == 'new_participants':
            for participant_id in v:
                event_to_edit.participants.append(
                    User.query.filter(User.id == participant_id).one())
        elif k == 'all_participants':
            del event_to_edit.participants[:]
            for participant_id in v:
                event_to_edit.participants.append(User.query.filter(User.id == participant_id).one())
        elif k == 'del_participants':
            conn = db.session.connection()
            conn.execute(events_users.delete().where(
                events_users.c.user_id.in_(v)).where(
                events_users.c.event_id == event_to_edit.id))
            conn.close()
        elif k == 'new_transactions':
            for trans_id in v:
                event_to_edit.transactions.append(
                    Transaction.query.filter(Transaction.id == trans_id).one())
        elif k == 'all_transactions':
            del event_to_edit.transactions[:]
            for trans_id in v:
                event_to_edit.transactions.append(
                    Transaction.query.filter(Transaction.id == trans_id).one())
        elif k == 'del_transactions':
            for trans_id in v:
                edit_trans = Transaction.query.filter(Transaction.id == trans_id).one()
                edit_trans.event = None
                db.session.add(edit_trans)
        elif k == 'transactions' or k == 'participants':
            return 'needs to be "new_transactions" or "all_participants" or whatever', 422
        else:
            setattr(event_to_edit, k, v)
    db.session.add(event_to_edit)
    db.session.commit()

@app.route('/api/user/<int:userid>', methods = ['POST'])
def edit_user(userid):
    user_to_edit = User.query.filter(User.id == userid).first()
    if not user_to_edit:
        return 'no such user', 404
    for k,v in request.form.items():
        if k == 'password' or k == 'roles':
            return 'dumbass.', 403
        elif k == 'friends' or k == 'transactions' or k == 'events':
            return 'prefix that with new_ or all_ for append or replace', 422
        elif k == 'new_friends':
            for new_friend_id in v:
                new_friend = User.query.filter(User.id == new_friend_id).one()
                user_to_edit.friends.append(new_friend)
        elif k == 'all_friends':
            del user_to_edit.friends[:]
            for new_friend_id in v:
                new_friend = User.query.filter(User.id == new_friend_id).one()
                user_to_edit.friends.append(new_friend)
        elif k == 'del_friends':
            for old_friend_id in v:
                old_friend = User.query.filter(User.id == old_friend_id).one()
                user_to_edit.friends.remove(old_friend)
        elif k == 'new_transactions':
            for trans_id in v:
                user_to_edit.transactions.append(Transaction.query.filter(
                    Transaction.id == trans_id).one())
        elif k == 'all_transactions':
            del user_to_edit.transactions[:]
            for trans_id in v:
                user_to_edit.transactions.append(Transaction.query.filter(
                    Transaction.id == trans_id).one())
        elif k == 'del_transactions':
            conn = db.session.connection()
            conn.execute(transactions_users.delete().where(
                transactions_users.c.transaction_id.in_(v)).where(
                transactions_users.c.user_id == user_to_edit.id))
            conn.close()
        elif k == 'new_events':
            for event_id in v:
                new_event = Event.query.filter(Event.id == event_id).one()
                user_to_edit.events.append(new_event)
        elif k == 'all_events':
            del user_to_edit.events[:]
            for event_id in v:
                new_event = Event.query.filter(Event.id == event_id).one()
                user_to_edit.events.append(new_event)
        elif k == 'del_events':
            conn = db.session.connection()
            conn.execute(events_users.delete().where(
                events_users.c.event_id.in_(v)).where(
                events_users.c.user_id == user_to_edit.id))
            conn.close()
        else:
            setattr(user_to_edit, k, v)
    db.session.add(user_to_add)
    db.session.commit()

# Views
@app.route('/')
@login_required
def home():
    return render_template('home.html')

if __name__ == '__main__':
    app.run()
