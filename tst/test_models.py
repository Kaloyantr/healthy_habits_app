import unittest
from app import create_app, db
from src.models import User, Health

class TestModels(unittest.TestCase):

    def setUp(self):
        """Set up the app and test client"""
        self.app = create_app()
        self.client = self.app.test_client()
        self.app.config['TESTING'] = True
        self.app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///test.db'
        db.create_all()

    def tearDown(self):
        """Clean up after each test"""
        db.session.remove()
        db.drop_all()

    def test_user_model(self):
        """Test the User model"""
        user = User(username='testuser', email='test@example.com', password='password', firstname='Test', surname='User')
        db.session.add(user)
        db.session.commit()

        user_from_db = User.query.filter_by(username='testuser').first()
        self.assertIsNotNone(user_from_db)
        self.assertEqual(user_from_db.username, 'testuser')

    def test_health_model(self):
        """Test the Health model"""
        user = User(username='testuser', email='test@example.com', password='password', firstname='Test', surname='User')
        db.session.add(user)
        db.session.commit()

        health_data = Health(userid=user.id, date='2025-02-09', steps=5000, heartrate=75, calories=200)
        db.session.add(health_data)
        db.session.commit()

        health_from_db = Health.query.filter_by(userid=user.id).first()
        self.assertIsNotNone(health_from_db)
        self.assertEqual(health_from_db.steps, 5000)

if __name__ == '__main__':
    unittest.main()
