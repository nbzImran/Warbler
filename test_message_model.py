import os
from unittest import TestCase
from models import db, User, Message, Likes
from app import app


#set the test database URL
os.environ['DATABASE_URL'] = 'postgresql:///warbler-test'


# create tables

with app.app_context():
    db.drop_all()
    db.create_all()



class MessageModelTestCase(TestCase):
    """Test user suit for  the message model."""


    @classmethod
    def setUpClass(cls):
        """Set Up the test enviroment once."""
        with app.app_context():
            db.drop_all()
            db.create_all()


    def setUp(self):
        """Set Up test data before each test."""

        with app.app_context():
            db.session.rollback()
            User.query.delete()
            Message.query.delete()


            self.user1 = User.signup(
                username="user1",
                email="user1@test.com",
                password="password",
                image_url=None,
            )


            self.user2 = User.signup(
                username="user2",
                email="user2@test.com",
                password="password",
                image_url=None,
            )

            db.session.commit()

    
    def tearDown(self):
        """Clean up fouled transactions."""
        with app.app_context():
            db.session.rollback()

    def test_message_creation(self):
        """test creating a message."""

        with app.app_context():
            user = User.query.filter_by(username="user1").first()
            msg = Message(text="This is a test message", user_id=user.id)
            db.session.add(msg)
            db.session.commit()


            self.assertEqual(msg.text, "This is a test message")
            self.assertEqual(msg.user_id, user.id)
            self.assertIsNotNone(msg.timestamp)


    def test_message_user_relationship(self):
        """Test the relationship between Message and User."""
        with app.app_context():
            user = User.query.filter_by(username="user1").first()
            msg = Message(text="this is another test message", user_id=user.id)
            db.session.add(msg)
            db.session.commit()

            self.assertEqual(msg.user.id, user.id)
            self.assertIn(msg, user.messages)