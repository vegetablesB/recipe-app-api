"""
Test custom Django commands
"""
from unittest.mock import patch

from psycopg2 import OperationalError as Psycopy2Error

from django.core.management import call_command
from django.db.utils import OperationalError
from django.test import SimpleTestCase


@patch('core.management.commands.wait_for_db.Command.check')
class CommandsTests(SimpleTestCase):
    """Test custom Django commands"""

    def test_wait_for_db_ready(self, mock_check):
        """Test waiting for db when db is available"""
        mock_check.return_value = True
        call_command('wait_for_db')

        mock_check.assert_called_once_with(database='default')
