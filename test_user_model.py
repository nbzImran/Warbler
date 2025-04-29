"""User model tests."""

# run these tests like:
#
#    python -m unittest test_user_model.py


import os
from unittest import TestCase

from models import db, User, Message, Follows, Likes

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()


class UserModelTestCase(TestCase):
    """Test views for messages."""

    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.drop_all()
            db.create_all()

            user1 = User.signup("user1", "user1@test.com", "password", None)
            user2 = User.signup("user2", "user2@test.com", "password", None)

            db.session.commit()
        
            self.user1 = User.query.get(user1.id)
            self.user2 = User.query.get(user2.id)


            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()

    def tearDown(self):
        """clean up any fouled transactions."""
        with app.app_context():
            db.session.rollback()


    def test_user_model(self):
        """Does basic model work?"""
        with app.app_context():
            u = User(
                email="test@test.com",
                username="testuser",
                password="HASHED_PASSWORD"
            )

            db.session.add(u)
            db.session.commit()

            # User should have no messages & no followers
            self.assertEqual(len(u.messages), 0)
            self.assertEqual(len(u.followers), 0)

    
    def test_is_following(self):
        """Does is_following successfully detect when user1 is following user2?"""

        with app.app_context():
            user1 = User.query.get(self.user1.id)
            user2 = User.query.get(self.user2.id)


            user1.following.append(user2)
            db.session.commit()

            self.assertTrue(user1.is_following(user2))
            self.assertFalse(user2.is_following(user1))

    def test_is_followed_by(self):
        """Does is_followed_by successfully detect when user1 is followed by user2?"""

        with app.app_context():
            user1 = User.query.get(self.user1.id)
            user2 = User.query.get(self.user2.id)


            user2.following.append(user1)
            db.session.commit()

            self.assertTrue(user1.is_followed_by(user2))
            self.assertFalse(user2.is_followed_by(user1))

    def test_user_signup(self):
        """Does User.signup successfully create a new user given valid credentials?"""

        with app.app_context():
            new_user = User.signup("testuser", "test@test.com", "password", None)
            db.session.commit()

            self.assertIsNotNone(User.query.get(new_user.id))
            self.assertEqual(new_user.username, "testuser")
            self.assertNotEqual(new_user.password, "password")  # Ensure password is hashed

    def test_user_signup_invalid(self):
        """Does User.signup fail to create a user if validations fail?"""

        with app.app_context():
            with self.assertRaises(Exception):
                User.signup(None, "invalid@test.com", "password", None)
                db.session.commit()

            with self.assertRaises(Exception):
                User.signup("testuser", None, "password", None)
                db.session.commit()

    def test_user_authenticate_valid(self):
        """Does User.authenticate return a user when given valid credentials?"""

        with app.app_context():
            user = User.authenticate("user1", "password")
            self.assertIsNotNone(user)
            self.assertEqual(user.username, "user1")

    def test_user_authenticate_invalid_username(self):
        """Does User.authenticate fail to return a user when the username is invalid?"""

        with app.app_context():
            user = User.authenticate("invaliduser", "password")
            self.assertFalse(user)

    def test_user_authenticate_invalid_password(self):
        """Does User.authenticate fail to return a user when the password is invalid?"""

        with app.app_context():
            user = User.authenticate("user1", "wrongpassword")
            self.assertFalse(user)