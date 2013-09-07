import sys
from main import db

if __name__ == '__main__':
    if len(sys.argv) > 1 and sys.argv[1] == 'createonly':
        print 'creating...'
        db.create_all()
    else:
        print 'dropping all tables...'
        db.drop_all()
        print 'creating all tables...'
        db.create_all()
