import datetime
import os
import json
import numpy
from prettydate import pretty_date
from flask import Flask, render_template, request
from flask.ext.sqlalchemy import SQLAlchemy
from flask.ext.security import Security, SQLAlchemyUserDatastore, \
    UserMixin, RoleMixin, login_required
from sqlalchemy.orm import class_mapper
from flask_security.core import current_user
from flask_security.forms import RegisterForm, TextField, Required

venmo_url = 'https://api.venmo.com/oauth/authorize?client_id=1351&scope=access_profile&response_type=code'

dthandler = lambda obj: pretty_date(obj) if isinstance(obj, datetime.datetime) else None
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

class SpecialRegisterForm(RegisterForm):
    name = TextField('Full Name')

class Role(db.Model, RoleMixin):
    id = db.Column(db.Integer(), primary_key=True)
    name = db.Column(db.String(80), unique=True)
    description = db.Column(db.String(255))
admin_role = None

friends = db.Table('friends',
        db.Column('f1_id', db.Integer(), db.ForeignKey('user.id')),
        db.Column('f2_id', db.Integer(), db.ForeignKey('user.id')))

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(255), unique=True)
    name = db.Column(db.String(255))
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
    name = db.Column(db.String(255), nullable=True)
    description = db.Column(db.String(1024), nullable=True)
    vendor = db.Column(db.String(255), nullable=True)
    amount_cents = db.Column(db.Integer, nullable=False)
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
    settled = db.Column(db.Boolean, default=False)
    end_date = db.Column(db.DateTime, default = lambda: datetime.datetime.now()
            + datetime.timedelta(days=2))

# Setup Flask-Security
user_datastore = SQLAlchemyUserDatastore(db, User, Role)
security = Security(app, user_datastore, register_form = SpecialRegisterForm)

@security.context_processor
def security_register_processor():
    return dict(user=current_user)

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

@app.route('/api/user/<int:userid>/events', methods = ['GET'])
def get_events_from_userid(userid):
    user = User.query.filter(User.id == userid).first()
    if not user:
        return 'user not found', 404
    return json.dumps([get_event_dict(event.id)
        for event in user.events], default=dthandler)

def get_friends(userid):
    results = db.session.execute(friends.select(friends.c.f1_id == userid)).fetchall()
    return [f2_id for f1_id, f2_id in results]

@app.route('/api/transaction/<int:transid>', methods = ['GET'])
def display_transaction_data(transid):
    transaction_dict = get_transaction_dict(transid)
    return json.dumps(transaction_dict, default=dthandler)

def get_transaction_dict(transid):
    transaction = Transaction.query.filter(Transaction.id == transid).first()
    if not transaction:
        return 'transaction not found', 404
    transaction_dict = asdict(transaction)
    transaction_dict['creator'] = get_user_data(transaction.creator.id)
    transaction_dict['participants'] = [asdict(participant)
            for participant in transaction.participants]
    return transaction_dict

@app.route('/api/event/<int:eventid>', methods = ['GET'])
def display_event_data(eventid):
    event_dict = get_event_dict(eventid)
    return json.dumps(event_dict, default=dthandler)

def get_event_dict(eventid):
    event = Event.query.filter(Event.id == eventid).first()
    if not event:
        return 'event not found', 404
    event_dict = asdict(event)
    event_dict['transactions'] = [get_transaction_dict(transaction.id)
            for transaction in event.transactions]
    event_dict['participants'] = [asdict(participant)
            for participant in event.participants]
    event_dict['creator'] = asdict(event.creator)
    return event_dict

@app.route('/api/transaction', methods = ['POST'])
@login_required
def new_transaction():
    modified_form = request.form.copy()
    participant_ids = [current_user.id]
    if 'participants[]' in modified_form:
        participant_ids += modified_form.getlist('participants[]')
        del modified_form['participants[]']
    modified_form['creator_id'] = current_user.id
    transaction = Transaction(name=modified_form.get('name'),
            description = modified_form.get('description'),
            event_id = modified_form.get('event_id'),
            creator_id = modified_form.get('creator_id'),
            vendor = modified_form.get('vendor'),
            amount_cents = modified_form.get('amount_cents')
            )
    users = User.query.filter(User.id.in_(participant_ids)).all()
    for user in users:
        transaction.participants.append(user)
    db.session.add(transaction)
    db.session.commit()
    return display_transaction_data(transaction.id)

@app.route('/api/event', methods = ['POST'])
@login_required
def new_event():
    modified_form = request.form.copy()
    participant_ids = [current_user.id]
    if 'participants[]' in modified_form:
        participant_ids += modified_form.getlist('participants[]')
        del modified_form['participants[]']
    transaction_ids = []
    if 'transactions[]' in modified_form:
        transaction_ids = modified_form.getlist('transactions[]')
        del modified_form['transactions[]']
    modified_form['creator_id'] = current_user.id
    event = Event(name=modified_form.get('name'),
            description = modified_form.get('description'),
            creator_id = modified_form.get('creator_id')
            )
    db.session.add(event)
    db.session.commit()
    for transaction_id in transaction_ids:
        transaction = Transaction.query.filter(Transaction.id == transaction_id).one()
        transaction.event = event
        db.session.add(transaction)
    users = User.query.filter(User.id.in_(participant_ids)).all()
    for user in users:
        event.participants.append(user)
    db.session.add(event)
    db.session.commit()
    return display_event_data(event.id)

@app.route('/api/transaction/<int:transid>', methods= ['POST'])
@login_required
def edit_transaction(transid):
    trans_to_edit = Transaction.query.filter(Transaction.id == transid).first()
    if not trans_to_edit:
        return 'no such transaction', 404
    if current_user not in trans_to_edit.participants and current_user != trans_to_edit.creator:
        return 'not authorized', 403
    for k,v in request.form.iterlists():
        if len(v) == 1 and not k.endswith('participants'):
            v = v[0]
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
            db.session.execute(transactions_users.delete().where(
                transactions_users.c.user_id.in_(v)).where(
                transactions_users.c.transaction_id == trans_to_edit.id))
        else:
            setattr(trans_to_edit, k, v)
    db.session.add(trans_to_edit)
    db.session.commit()
    return display_transaction_data(trans_to_edit.id)

@app.route('/api/event/<int:eventid>', methods=['POST'])
@login_required
def edit_event(eventid):
    event_to_edit = Event.query.filter(Event.id == eventid).first()
    if not event_to_edit:
        return 'no such event', 404
    if current_user not in event_to_edit.participants:
        return 'not authorized', 403
    for k,v in request.form.iterlists():
        if len(v) == 1 and not k.endswith('participants') and not k.endswith('transactions'):
            v = v[0]
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
            db.session.execute(events_users.delete().where(
                events_users.c.user_id.in_(v)).where(
                events_users.c.event_id == event_to_edit.id))
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
    return display_event_data(event_to_edit.id)

@app.route('/api/event/<int:eventid>/adduser', methods = ['POST'])
@login_required
def add_user(eventid):
    user_email = request.form.get('email')
    user = User.query.filter(User.email == user_email).first()
    if not user:
        return json.dumps({'error' : True})
    event = Event.query.filter(Event.id == eventid).first()
    if not event:
        return json.dumps({'error' : True, 'message' : 'jesus christ what did you doooooooo'})
    event.participants.append(user)
    db.session.add(event)
    db.session.commit()
    event_dict = get_event_dict(eventid)
    event_dict['error'] = False
    return json.dumps(event_dict, default=dthandler)

@app.route('/api/user/<int:userid>', methods = ['POST'])
@login_required
def edit_user(userid):
    if userid != current_user.id and admin_role not in current_user.roles:
        return 'NOT AUTHORIZED', 403
    user_to_edit = User.query.filter(User.id == userid).first()
    if not user_to_edit:
        return 'no such user', 404
    for k,v in request.form.items():
        if (len(v) == 1 and not k.endswith('friends')
                and not k.endswith('events') and not k.endswith('transactions')):
            v = v[0]
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
            db.session.execute(transactions_users.delete().where(
                transactions_users.c.transaction_id.in_(v)).where(
                transactions_users.c.user_id == user_to_edit.id))
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
            db.session.execute(events_users.delete().where(
                events_users.c.event_id.in_(v)).where(
                events_users.c.user_id == user_to_edit.id))
        else:
            setattr(user_to_edit, k, v)
    db.session.add(user_to_edit)
    db.session.commit()
    return display_user_data(user_to_edit.id)

#Venmo
@app.route('/api/venmo/accesstoken', methods = ['GET'])
@login_required
def getAccessToken():
    code = request.args.get('code')
    values = {'code':code, 'client_id':client_id, 'client_secret':client_secret}
    data = urllib.urlencode(values)
    request = urllib2.Request('https://api.venmo.com/oauth/access_token')
    try:
        res = urllib2.urlopen(request, data)
    except:
        return 'Could not retrieve access_token', 405
    rJson = simplejson.load(res)
    access_token = rJson['access_token']
    user = User.query.filter(User.id == current_user.id).one()
    user.venmo_key = access_token
    db.session.add(user)
    db.commit()
    return redirect(url_for('account'))

@app.route('/api/venmo/pay', methods = ['POST'])
def payUser(recipient_id, amount, user_id):
    recipient_id = request.form.get(recipient_id)
    amount = request.form.get(amount)
    user_id = request.form.get(user_id)
    user = User.query.filter(User.id == user_id).one()
    access_token = user.venmo_key
    data = urllib.urlencode({'access_token':"bZZCt4H3vbh5JgSXMBMh2mnUBT7hDb7a", 'user_id':user_id, "amount":amount})
    request = urllib2.Request("https://sandbox-api.venmo.com/payments")
    res = urllib2.urlopen(request, data)

def settle():
    ##find creator
    event = Event.query.filter(Event.id == eventid).first()
    creator = event.creator

    ##find all users involved
    participants = event.participants

    ##add money for each transaction
    partysize = participants.size + 1
    payTable = zeros( (partysize, partysize), dtype=int16)
    translation_number = 1
    for eventparticipant in participants:
        payTable[0][translation_number] = eventparticipant
        payTable[translation_number][0] = eventparticipant
    transactions = Transaction.query.filter(Transaction.event_id == eventid).all()
    for transaction in transactions:
        amount = transaction.amount_cents
        transparticipants = transaction.participants
        transpartysize = transparticipants.size
        creator = transaction.creator
        iou = amount/transpartysize
        creatorIndex = 1
        for index in range(partysize):
            if (payTable[0][index] == creator):
                creatorIndex = index
        for index in range(partysize):
            if (payTable[0][index] in transparticipants):
                payTable[creatorIndex][index] += iou

    ##calculate who owes money to whom
    for xindex in range(partysize):
        for yindex in range(xindex, partysize):
            if payTable[xindex][yindex] > payTable[yindex][xindex]:
                payTable[xindex][yindex] -= payTable[yindex][xindex]
                payTable[yindex][xindex] = 0
            else:
                payTable[yindex][xindex] -= payTable[xindex][yindex]
                payTable[xindex][yindex] = 0
    return payTable

# Views
@app.route('/')
def home():
    return render_template('home.html', user=current_user)

@app.route('/account')
@login_required
def account():
    return render_template('account.html', user=current_user)

@app.route('/event/<id>')
@login_required
def event(id):
    event_obj = Event.query.filter(Event.id == id).first()
    if not event_obj:
        return 'not found', 404
    return render_template('event.html', user=current_user, eventID=id, event=event_obj)

if __name__ == '__main__':
    admin_role = Role.query.filter(Role.name == 'admin').first()
    if not admin_role:
        admin_role = Role(name='admin', description='admin user')
        db.session.add(admin_role)
        db.session.commit()
    app.run()
