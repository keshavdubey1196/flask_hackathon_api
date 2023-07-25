from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
db = SQLAlchemy()


# Association table for MtoM rel bw hackathon and users
user_hackathons = db.Table('user_hackathons',
                           db.Column("id", db.Integer(), primary_key=True,
                                     autoincrement=True),
                           db.Column('user_id', db.Integer(), db.ForeignKey(
                               'users.id'), primary_key=True),
                           db.Column(
                               'hackathon_id', db.Integer(),
                               db.ForeignKey('hackathons.id'),
                               primary_key=True))


class User(db.Model):
    __tablename__ = 'users'

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    name = db.Column(db.String(100), nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.String(200), unique=True, nullable=False)
    created_at = db.Column(
        db.DateTime(), default=datetime.utcnow)
    id_admin = db.Column(db.Boolean(), default=False)

    created_hackathons = db.relationship(
        'Hackathon', backref='creator', lazy=True)

    participated_hackathons = db.relationship(
        'Hackathon', secondary=user_hackathons,
        backref='participants', lazy=True)


class Hackathon(db.Model):
    __tablename__ = 'hackathons'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.String(500))
    bg_image = db.Column(db.String(200), nullable=True)
    hakthon_img = db.Column(db.String(200), nullable=True)
    submission_type = db.Column(db.String(10), nullable=False, default="File")
    rewards = db.Column(db.Integer(), nullable=True, default=500)
    created_at = db.Column(
        db.DateTime(), default=datetime.utcnow)
    start_datetime = db.Column(db.DateTime(), nullable=True)
    end_datetime = db.Column(db.DateTime(), nullable=True)
    creator_id = db.Column(db.Integer(), db.ForeignKey('users.id'))


class Submission(db.Model):
    __tablename__ = 'submissions'

    id = db.Column(db.Integer(), primary_key=True, autoincrement=True)
    file = db.Column(db.String(200), nullable=True)
    url = db.Column(db.String(300), nullable=True)
    created_at = db.Column(
        db.DateTime(), default=datetime.utcnow)
    user_id = db.Column(db.Integer(), db.ForeignKey(
        'users.id'), nullable=False)
    hackathon_id = db.Column(db.Integer(), db.ForeignKey(
        'hackathons.id'), nullable=True)

    user = db.relationship('User', backref='submissions', lazy=True)
    hackathon = db.relationship('Hackathon', backref='submissions', lazy=True)


def init_db(app):
    with app.app_context():
        db.init_app(app)
        db.create_all()
