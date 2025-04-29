import os
from unittest import TestCase
from models import db, User, Message, Follows
from app import app, CURR_USER_KEY

# Set the test database URL
os.environ['DATABASE_URL'] = "postgresql:///warbler-test"

# Create tables
with app.app_context():
    db.drop_all()
    db.create_all()


class UserViewsTestCase(TestCase):
    """Test suite for user-related views."""

    @classmethod
    def setUpClass(cls):
        """Set up the test environment once."""
        with app.app_context():
            db.drop_all()
            db.create_all()

    def setUp(self):
        """Set up test data before each test."""
        with app.app_context():
            db.session.rollback()
            User.query.delete()
            Message.query.delete()
            Follows.query.delete()

            self.client = app.test_client()

            self.user1 = User.signup(
                "user1",
                "user1@test.com",
                "password",
                None,
            )

            self.user2 = User.signup(
                "user2",
                "user2@test.com",
                "password",
                None
            )

            db.session.commit()

    def tearDown(self):
        """Clean up fouled transactions."""
        with app.app_context():
            db.session.rollback()

    def test_user_list(self):
        """Can a user see the user list?"""
        with self.client as c:
            resp = c.get("/users")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user1", resp.get_data(as_text=True))
            self.assertIn("user2", resp.get_data(as_text=True))

    def test_user_profile(self):
        """Can a user view another user's profile?"""
        with app.app_context():
            user1 = User.query.filter_by(username="user1").first()
        with self.client as c:
            resp = c.get(f"/users/{user1.id}")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user1", resp.get_data(as_text=True))

    def test_following(self):
        """Can a user view their following list?"""
        with app.app_context():
            user1 = User.signup(username="testuser1",email="testuser1@test.com", password="password", image_url=None)
            user2 = User.signup(username="testuser2",email="testuser2@test.com", password="password", image_url=None)
            user1.following.append(user2)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user1.id

            resp = c.get(f"/users/{user1.id}/following")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", resp.get_data(as_text=True))

    def test_followers(self):
        """Can a user view their followers list?"""
        with app.app_context():
            user1 = User.query.filter_by(username="user1").first()
            user2 = User.query.filter_by(username="user2").first()

            user2.following.append(user1)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user1.id

            resp = c.get(f"/users/{user1.id}/followers")
            self.assertEqual(resp.status_code, 200)
            self.assertIn("user2", resp.get_data(as_text=True))

    def test_follow(self):
        """Can a user follow another user?"""
        with app.app_context():
            user1 = User.query.filter_by(username="user1").first()
            user2 = User.query.filter_by(username="user2").first()

            with self.client as c:
                with c.session_transaction() as sess:
                 sess[CURR_USER_KEY] = user1.id

            resp = c.post(f"/users/follow/{user2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with app.app_context():
                self.assertIn(user2, user1.following)

    def test_unfollow(self):
        """Can a user unfollow another user?"""
        with app.app_context():
            user1 = User.query.filter_by(username="user1").first()
            user2 = User.query.filter_by(username="user2").first()

            user1.following.append(user2)
            db.session.commit()

            with self.client as c:
                with c.session_transaction() as sess:
                    sess[CURR_USER_KEY] = user1.id

            resp = c.post(f"/users/stop-following/{user2.id}", follow_redirects=True)
            self.assertEqual(resp.status_code, 200)

            with app.app_context():
                self.assertNotIn(user2, user1.following)

    def test_unauthorized_follow(self):
        """Can an unauthorized user follow another user?"""
        with app.app_context():
            user2 = User.query.filter_by(username="user2").first()

            with self.client as c:
                resp = c.post(f"/users/follow/{user2.id}", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", resp.get_data(as_text=True))

    def test_unauthorized_unfollow(self):
        """Can an unauthorized user unfollow another user?"""
        with app.app_context():
            user1 = User.query.filter_by(username="user1").first()
            user2 = User.query.filter_by(username="user2").first()

            user1.following.append(user2)
            db.session.commit()

            with self.client as c:
                resp = c.post(f"/users/stop-following/{user2.id}", follow_redirects=True)
                self.assertEqual(resp.status_code, 200)
                self.assertIn("Access unauthorized", resp.get_data(as_text=True))
