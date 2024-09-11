from app import app
import unittest
from unittest.mock import patch, MagicMock
from database import Database
import sqlite3





#######################################################
#                                                     #
#                  TESTS PAGES HTML                   #
#                                                     #
#######################################################

# Tests pour pages valides
#------------------------------------------------------

def test_index_route():
    response = app.test_client().get('/')
    assert response.status_code == 200

def test_login_route():
    response = app.test_client().get('/login')
    assert response.status_code == 200

def test_confirmation_route():
    response = app.test_client().get('/confirmation/ok')
    assert response.status_code == 200

def test_error_route():
    response = app.test_client().get('/error/ok')
    assert response.status_code == 200

#Test pour pages invalides
#------------------------------------------------------

def test_route_invalid():
    response = app.test_client().get('/invalid_route')
    assert response.status_code == 404





#######################################################
#                                                     #
#                      TESTS BD                       #
#                                                     #
#######################################################


class TestDatabase(unittest.TestCase):
    @patch('sqlite3.connect')
    def test_get_connection_new(self, mock_connect):
        mock_connect.return_value = MagicMock(spec=sqlite3.Connection)
        db = Database()

        connection = db.get_connection()

        mock_connect.assert_called_once_with('db/database.db')
        self.assertEqual(connection, mock_connect.return_value)
        self.assertIsNotNone(db.connection)

    @patch('sqlite3.connect')
    def test_get_connection_existing(self, mock_connect):
        mock_connect.return_value = MagicMock(spec=sqlite3.Connection)
        db = Database()
        existing_connection = db.get_connection()

        connection = db.get_connection()

        mock_connect.assert_called_once_with('db/database.db')
        self.assertEqual(connection, existing_connection)
        self.assertIs(connection, existing_connection)





#######################################################
#                                                     #
#                      TESTS FORMS                    #
#                                                     #
#######################################################


class FormTestCase(unittest.TestCase):
    def setUp(self):
        app.config['TESTING'] = True
        self.client = app.test_client()

    # Test pour ResetRequestForm
    @patch('form.ResetRequestForm')
    def test_reset_request_form(self, MockResetRequestForm):
        mock_form_instance = MockResetRequestForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        form_data = {'email': 'test@example.com'}
        response = self.client.post('/reset_password', data=form_data)

        self.assertEqual(response.status_code, 200)

    # Test pour GenerationForm
    @patch('form.GenerationForm')
    def test_generation_form(self, MockGenerationForm):
        mock_form_instance = MockGenerationForm.return_value
        mock_form_instance.validate_on_submit.return_value = True

        form_data = {'attraction1': 'cafe', 'attraction2' : 'museum', 'rayon' : '250', 'coordonnees': '1', 'Optimisation': '1', 'Deplacement': 'DRIVE'}
        response = self.client.post('/generation', data=form_data)

        self.assertEqual(response.status_code, 200)
