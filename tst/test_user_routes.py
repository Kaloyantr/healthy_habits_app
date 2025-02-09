import unittest
from app import create_app, db
from src.models import User

class TestUserRoutes(unittest.TestCase):

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

    def test_register(self):
        """Test user registration"""
        response = self.client.post('/register_action', data={
            'username': 'testuser',
            'email': 'test@example.com',
            'password': 'password',
            'firstname': 'Test',
            'surname': 'User'
        })
        self.assertEqual(response.status_code, 302)  # Redirect after successful registration
        self.assertIn(b'Registration successful!', response.data)

    def test_login(self):
        """Test user login"""
        user = User(username='testuser', email='test@example.com', password='password', firstname='Test', surname='User')
        db.session.add(user)
        db.session.commit()
        
        response = self.client.post('/login_action', data={
            'username': 'testuser',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 302)  # Redirect to start menu after successful login
        self.assertIn(b'Success', response.data)

    def test_logout(self):
        """Test user logout"""
        response = self.client.get('/logout')
        self.assertEqual(response.status_code, 302)  # Should redirect to home after logging out
        self.assertIn(b'Home', response.data)

if __name__ == '__main__':
    unittest.main()
