import unittest
from src.utils import allowed_file

class TestUtils(unittest.TestCase):

    def test_allowed_file(self):
        """Test the allowed_file utility function"""
        valid_files = ['image.png', 'photo.jpg', 'pic.jpeg', 'graph.gif']
        invalid_files = ['document.pdf', 'text.txt', 'file.exe']

        for file in valid_files:
            self.assertTrue(allowed_file(file))
        
        for file in invalid_files:
            self.assertFalse(allowed_file(file))

if __name__ == '__main__':
    unittest.main()
