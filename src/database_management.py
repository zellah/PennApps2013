import sys
from main import db, User

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'createonly':
        print 'creating...'
        db.create_all()
    elif len(sys.argv) > 1 and sys.argv[1] == 'testdata':
        u1 = User(email = 'ndm25@case.edu', password = 'password',
                name='Nathan', active = True, venmo_key = 'potatoes')
        u2 = User(email = 'origaminut@gmail.com', password = 'password',
                name='Zella', active = True, venmo_key = 'potatoes2')
        u3 = User(email = 'steve@something.edu', password = 'hunter2',
                name='Steve', active = True, venmo_key = 'potatoes3')
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
        u1.friends.append(u2)
        u2.friends.append(u1)
        u2.friends.append(u3)
        u3.friends.append(u2)
        db.session.add(u1)
        db.session.add(u2)
        db.session.add(u3)
        db.session.commit()
    else:
        print 'dropping all tables...'
        db.drop_all()
        print 'creating all tables...'
        db.create_all()
