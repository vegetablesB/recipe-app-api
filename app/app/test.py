"""
Sample test file
"""

from django.test import SimpleTestCase

from app import calc


class CalcTests(SimpleTestCase):
    """Sample test class"""

    def test_add_numbers(self):
        """Sample test method"""
        self.assertEqual(calc.add(3, 8), 11)
        self.assertEqual(calc.add(3, 8), 11)
