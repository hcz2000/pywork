import os
#from flask_migrate import Migrate, upgrade
from app import create_app, db
from app.models import User, Role, Permission
from flask_script import Manager,Shell

app = create_app(os.getenv('FLASK_CONFIG') or 'development')
manager=Manager(app)
#migrate = Migrate(app, db)


@app.shell_context_processor
def make_shell_context():
    return dict(db=db, User=User, Role=Role,Permission=Permission)
manager.add_command("shell",Shell(make_context=make_shell_context))

if __name__== '__main__':
    #manager.run()
    app.run()
