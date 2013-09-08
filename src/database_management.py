import sys
from main import db, User, Transaction, Event

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'createonly':
        print 'creating...'
        db.create_all()
    elif len(sys.argv) > 1 and sys.argv[1] == 'testdata':
        db.drop_all()
        db.create_all()
        u1 = User(email = 'ndm25@case.edu', password = 'password',
                name='Nathan', active = True, venmo_key = 'potatoes')
        u2 = User(email = 'origaminut@gmail.com', password = 'password',
                name='Zella', active = True, venmo_key = 'potatoes2')
        u3 = User(email = 'steve@something.edu', password = 'hunter2',
                name='Steve', active = True, venmo_key = 'potatoes3')
        u4 = User(email = 'spiderman@aol.com', password='friendlyneighborhood',
                name='Spiderman', active=True, venmo_key='banananananas')

        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.add(u4)
        db.session.commit()
        u1.friends.append(u2)
        u2.friends.append(u1)
        u2.friends.append(u3)
        u3.friends.append(u2)
        u2.friends.append(u4)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
        t1 = Transaction(name='Pizza', description='something', vendor='somewhere',
                amount_cents = 1234, creator = u1)
        t1.participants.append(u1)
        t1.participants.append(u2)
        t2 = Transaction(name='Burgers', description='whoah', vendor='somewhere2',
                amount_cents = 5555, creator = u2)
        t2.participants.append(u3)
        t2.participants.append(u2)
        db.session.add(t1)
        db.session.add(t2)
        db.session.commit()
        e1 = Event(name='Pennapps', description='sleeping? bah.', creator = u1,
                participants = [u1,u2,u3], settled=False)
        e1.transactions.append(t1)
        e1.transactions.append(t2)
        db.session.add(e1)
        db.session.commit()
    else:
        print 'dropping all tables...'
        db.drop_all()
        print 'creating all tables...'
        db.create_all()
