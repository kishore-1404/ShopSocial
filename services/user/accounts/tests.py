from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

class UserRegistrationTests(APITestCase):
	"""Tests for the user registration endpoint."""
	def test_register_user_success(self):
		url = reverse('register')
		data = {
			'username': 'testuser',
			'password': 'testpass123',
			'email': 'test@example.com'
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertIn('id', response.data or {})
