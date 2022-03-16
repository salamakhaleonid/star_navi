from flask import Flask
from test_task.models import db

app = Flask(__name__)
app.config['SECRET_KEY'] = 'your secret key'
# database name
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///Database.db' # this will do for the test project
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = True
db.init_app(app)

import test_task.views

