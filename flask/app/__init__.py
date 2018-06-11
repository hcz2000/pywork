from flask import Flask
from flask_sqlalchemy import SQLAlchemy
from config import config

app=Flask(__name__)
#app.config['SQLALCHEMY_DATABASE_URI'] ='mysql+mysqlconnector://root:@localhost:3306/test'
#app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
#app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
#app.config['FLASKY_ADMIN']='huangchangzhan@hotmail.com'
#app.config['SECRECT_KEY']='hard to guess string'
 
db = SQLAlchemy()

def create_app(config_name):
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    config[config_name].init_app(app)
    print(app.config['SQLALCHEMY_DATABASE_URI'])
    db.init_app(app)
    from .api_1_0 import api as api_1_0_blueprint
    app.register_blueprint(api_1_0_blueprint,url_prefix='/api/v1.0')
    return app
