"""Message View tests."""

# run these tests like:
#
#    FLASK_ENV=production python -m unittest test_message_views.py


import os
from unittest import TestCase

from models import db, connect_db, Message, User, Likes

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
            Message.query.delete()

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


    def test_add_message(self):
        """Can use add a message?"""

        with app.app_context():
                    # re-query the testuser to ensure it is bound to the session.
                    testuser = User.query.filter_by(username="testuser").first()

        # Since we need to change the session to mimic logging in,
        # we need to use the changing-session trick:

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser.id

            # Now, that session setting is saved, so we can have
            # the rest of ours test

            resp = c.post("/messages/new", data={"text": "Hello"})

            # Make sure it redirects
            self.assertEqual(resp.status_code, 302)
          
            with app.app_context():
                msg = Message.query.one()
                self.assertEqual(msg.text, "Hello")
                self.assertEqual(msg.user_id, testuser.id)



    def test_add_message_unauthorized(self):
        """Can a unautheorized user add a message?"""
            



        with self.client as c:
            resp = c.post("/messages/new", data={"text": "Hello"}, follow_redirects=True )
            self.assertEqual(resp.status_code, 200)
            self.assertIn("Access unauthorized", str(resp.data))

            with app.app_context():
                self.assertEqual(Message.query.count(), 0)



    def test_delete_message(self):
        """can a logged in user delet thier own message?"""


        with app.app_context():
                    # re-query the testuser to ensure it is bound to the session.
                    testuser = User.query.filter_by(username="testuser").first()


        with app.app_context():
            msg = Message(text="hello", user_id=testuser.id)
            db.session.add(msg)
            db.session.commit()

            msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser.id

            resp = c.post(f"/messages/{msg_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with app.app_context():
                self.assertEqual(Message.query.count(), 0)


    def test_delete_message_unauthorized(self):
        """Can a user delete another user's message?"""

        with app.app_context():
                    # re-query the testuser, and other_user to ensure it is bound to the session.
                    other_user = User.query.filter_by(username="other_user").first()
                    testuser = User.query.filter_by(username="testuser").first()
                    self.assertIsNotNone(other_user, "other_user should exist")
                    self.assertIsNotNone(testuser, "testuser should exist in database")
                    


        with app.app_context():
                    msg = Message(text="Hello", user_id=other_user.id)
                    db.session.add(msg)
                    db.session.commit()

                    msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser.id


            resp = c.post(f"/messages/{msg_id}/delete", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            # response_text = resp.get_data(as_text=True)
            # self.assertIn("Access unauthorized", response_text)

            with app.app_context():
                self.assertEqual(Message.query.count(), 0)

    def test_like_message(self):
        """Can a user like another user's message?"""


        with app.app_context():
                    # re-query the testuser, and other_user to ensure it is bound to the session.
                    other_user = User.query.filter_by(username="other_user").first()
                    testuser = User.query.filter_by(username="testuser").first()
                    self.assertIsNotNone(other_user, "other_user should exist")
                    self.assertIsNotNone(testuser, "testuser should exist")
                    


        with app.app_context():
            msg = Message(text="Hello", user_id=other_user.id)
            db.session.add(msg)
            db.session.commit()

            msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser.id

            resp = c.post(f"/users/add_like/{msg_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with app.app_context():
                likes = Likes.query.filter_by(user_id=testuser.id).all()
                self.assertEqual(len(likes), 1)
                self.assertEqual(likes[0].message_id, msg_id)

    def test_like_own_message(self):
        """Ensure a user cannot like their own message."""

        with app.app_context():
                    # re-query the testuser to ensure it is bound to the session.
                    testuser = User.query.filter_by(username="testuser").first()


        with app.app_context():
            msg = Message(text="Hello", user_id=testuser.id)
            db.session.add(msg)
            db.session.commit()

            msg_id = msg.id

        with self.client as c:
            with c.session_transaction() as sess:
                sess[CURR_USER_KEY] = testuser.id

            resp = c.post(f"/users/add_like/{msg_id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)
            self.assertIn("You cannot like your own warble", str(resp.data))

            with app.app_context():
                likes = Likes.query.filter_by(user_id=testuser.id).all()
                self.assertEqual(len(likes), 0)

    def test_unlike_message(self):
        """Can a user unlike a message they previously liked?"""

        with app.app_context():
                    # re-query the testuser, and other_user to ensure it is bound to the session.
                    other_user = User.query.filter_by(username="other_user").first()
                    testuser = User.query.filter_by(username="testuser").first()
                    self.assertIsNotNone(other_user, "other_user should exist")
                    self.assertIsNotNone(testuser, "testuser should exist")
                    


       
                    msg = Message(text="Hello", user_id=other_user.id)

                    db.session.add(msg)
                    

                    testuser.likes.append(msg)
                    db.session.commit()

                    msg_id = msg.id

                    with self.client as c:
                        with c.session_transaction() as sess:
                            sess[CURR_USER_KEY] = testuser.id

                        resp = c.post(f"/users/remove_like/{msg_id}", follow_redirects=True)
                        self.assertEqual(resp.status_code, 200)

                    
                    likes = Likes.query.filter_by(user_id=testuser.id).all()
                    self.assertEqual(len(likes), 0)


