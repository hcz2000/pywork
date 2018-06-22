import os
#from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Role, Permission
from flask_script import Manager,Shell

app = create_app(os.getenv('FLASK_CONFIG') or 'development')

if __name__== '__main__':
    app.run()
