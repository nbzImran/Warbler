"""SQLAlchemy models for Warbler."""

from datetime import datetime

from flask_bcrypt import Bcrypt
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import check_password_hash, generate_password_hash

bcrypt = Bcrypt()
db = SQLAlchemy()


class Follows(db.Model):
    """Connection of a follower <-> followed_user."""

    __tablename__ = 'follows'

    user_being_followed_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )

    user_following_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete="cascade"),
        primary_key=True,
    )


class Likes(db.Model):
    """Mapping user likes to warbles."""

    __tablename__ = 'likes' 

    id = db.Column(
        db.Integer,
        primary_key=True
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='cascade')
    )

    message_id = db.Column(
        db.Integer,
        db.ForeignKey('messages.id', ondelete='cascade'),
        unique=True
    )


class User(db.Model):
    """User in the system."""

    __tablename__ = 'users'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    email = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    username = db.Column(
        db.Text,
        nullable=False,
        unique=True,
    )

    image_url = db.Column(
        db.Text,
        default="/static/images/default-pic.png",
    )

    header_image_url = db.Column(
        db.Text,
        default="/static/images/warbler-hero.jpg"
    )

    bio = db.Column(
        db.Text,
    )

    location = db.Column(
        db.Text,
    )

    password = db.Column(
        db.Text,
        nullable=False,
    )

    messages = db.relationship('Message', cascade='all, delete-orphan', overlaps="user")

    followers = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_being_followed_id == id),
        secondaryjoin=(Follows.user_following_id == id),
        overlaps="following",
    )

    following = db.relationship(
        "User",
        secondary="follows",
        primaryjoin=(Follows.user_following_id == id),
        secondaryjoin=(Follows.user_being_followed_id == id),
        overlaps="followers",
    )

    likes = db.relationship(
        'Message',
        secondary="likes"
    )

    def __repr__(self):
        return f"<User #{self.id}: {self.username}, {self.email}>"

    def is_followed_by(self, other_user):
        """Is this user followed by `other_user`?"""

        found_user_list = [user for user in self.followers if user == other_user]
        return len(found_user_list) == 1

    def is_following(self, other_user):
        """Is this user following `other_use`?"""

        found_user_list = [user for user in self.following if user == other_user]
        return len(found_user_list) == 1

    @classmethod
    def signup(cls, username, email, password, image_url):
        """Sign up user.

        Hashes password and adds user to system.
        """

        hashed_pwd = bcrypt.generate_password_hash(password).decode('UTF-8')

        user = User(
            username=username,
            email=email,
            password=hashed_pwd,
            image_url=image_url,
        )

        db.session.add(user)
        return user

    @classmethod
    def authenticate(cls, username, password):
        """Find user with `username` and `password`.

        This is a class method (call it on the class, not an individual user.)
        It searches for a user whose password hash matches this password
        and, if it finds such a user, returns that user object.

        If can't find matching user (or if password is wrong), returns False.
        """

        user = cls.query.filter_by(username=username).first()

        if user:
            is_auth = bcrypt.check_password_hash(user.password, password)
            if is_auth:
                return user

        return False
    
    @classmethod
    def change_password(self, current_password, new_password):
        """Change the user's password if the current passord is correct"""

        if not hasattr(self,'_pasword_cache'):
            self._password_cache = self.password # Cache the actual password value


        current_hased_password = self._password_value(self)

        if bcrypt.check_password_hash(current_hased_password, current_password):
            self.password = bcrypt.generate_password_hash(new_password).decode('UTF-8')
            db.session.commit()
            return True
        return False
    def _password_value(self):
        """helper to get the actual password value."""
        return db.session.query(User.password).filter_by(id=self.id).scalar()

class Message(db.Model):
    """An individual message ("warble")."""

    __tablename__ = 'messages'

    id = db.Column(
        db.Integer,
        primary_key=True,
    )

    text = db.Column(
        db.String(140),
        nullable=False,
    )

    timestamp = db.Column(
        db.DateTime,
        nullable=False,
        default=datetime.utcnow(),
    )

    user_id = db.Column(
        db.Integer,
        db.ForeignKey('users.id', ondelete='CASCADE'),
        nullable=False,
    )

    user = db.relationship('User')


class DirectMessage(db.Model):
    """Model for direct messages between users."""

    __tablename__ = "direct_messages"

    id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    sender_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    content = db.Column(db.Text, nullable=False)
    timestamp = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    sender = db.relationship("User", foreign_keys=[sender_id], backref="sent_messages")
    recipient = db.relationship("User", foreign_keys=[recipient_id], backref="received_messages")
    


def connect_db(app):
    """Connect this database to provided Flask app.

    You should call this in your Flask app.
    """

    db.app = app
    db.init_app(app)
