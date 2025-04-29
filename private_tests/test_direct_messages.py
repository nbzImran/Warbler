import os
from unittest import TestCase

from models import db, connect_db, DirectMessage, User

# BEFORE we import our app, let's set an environmental variable
# to use a different database for tests (we need to do this
# before we import our app, since that will have already
# connected to the database

os.environ['DATABASE_URL'] = "postgresql:///warbler-test"


# Now we can import app

from app import app, CURR_USER_KEY

# Create our tables (we do this here, so we only create the tables
# once for all tests --- in each test, we'll delete the data
# and create fresh new clean test data
with app.app_context():
    db.drop_all()
    db.create_all()

# Don't have WTForms use CSRF at all, since it's a pain to test

app.config['WTF_CSRF_ENABLED'] = False



class MessageViewTestCase(TestCase):
    """Test views for messages."""
    @classmethod
    def setUp(self):
        """Create test client, add sample data."""
        with app.app_context():
            db.session.rollback()
            db.drop_all()
            db.create_all()
            User.query.delete()
            DirectMessage.query.delete()

            self.client = app.test_client()

           

            self.testuser = User.signup(username="testuser",
                                    email="test@test.com",
                                    password="testuser",
                                    image_url=None)
            
            self.other_user = User.signup(username="other_user",
                email="other@test.com",
                password="otheruser",
                image_url=None)

            db.session.commit()


    def tearDown(self):
        """Rollback any fouled transactions."""
        with app.app_context():
            db.session.rollback()



    def test_send_message(self):
        """Can a logged-in user send a message?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.post("/messages/send", data={"recipient": "otheruser", "content": "Hello!"}, follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Message sent!", str(resp.data))

    def test_view_messages(self):
        """Can a logged-in user view their messages?"""
        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = self.testuser.id

            resp = c.get("/messages")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Inbox", str(resp.data))
