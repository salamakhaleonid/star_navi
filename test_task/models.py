from flask_sqlalchemy import SQLAlchemy
db = SQLAlchemy()

class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    name = db.Column(db.String(100))
    email = db.Column(db.String(70), unique=True)
    password = db.Column(db.String(80))
    creation_time = db.Column(db.DateTime(timezone=False))
    last_login_time = db.Column(db.DateTime(timezone=False))
    last_activity_time = db.Column(db.DateTime(timezone=False))

class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    public_id = db.Column(db.String(50), unique=True)
    text = db.Column(db.String(), nullable=False)
    user_public_id = db.Column(db.Integer, db.ForeignKey('user.public_id'),
        nullable=False)# post are created by users

class Like(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_public_id = db.Column(db.Integer, db.ForeignKey('user.public_id'),
                          nullable=False) # likes can only be created for posts by users
    post_public_id = db.Column(db.Integer, db.ForeignKey('post.public_id'),
                          nullable=False)
    creation_time = db.Column(db.DateTime(timezone=False))

