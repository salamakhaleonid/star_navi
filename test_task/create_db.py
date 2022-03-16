#this py is neaded to create a new db using table models in models
#Attention, if file exists it is not rewritten
from test_task import db,app
with app.app_context():
    db.create_all()