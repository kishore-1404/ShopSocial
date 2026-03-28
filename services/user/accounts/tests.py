import os

from django.urls import reverse
from django.contrib.auth.models import User
from rest_framework.test import APITestCase
from rest_framework import status

from .models import Follower, Post
from .service import get_feed, get_followers, get_following
from common.cache_service import reset_cache_client
from common.rate_limit import reset_rate_limiter

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

	def test_register_rejects_short_password(self):
		url = reverse('register')
		data = {
			'username': 'shortpass',
			'password': '123',
			'email': 'test@example.com'
		}
		response = self.client.post(url, data, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertIn('password', response.data)


class UserServiceViewTests(APITestCase):
	def setUp(self):
		self.user = User.objects.create_user(username='alice', password='alice-pass')
		self.other = User.objects.create_user(username='bob', password='bob-pass')
		self.client.force_authenticate(user=self.user)

	def test_follow_requires_user_id(self):
		url = reverse('follow-user')
		response = self.client.post(url, {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid follow payload')
		self.assertIn('errors', response.data)

	def test_follow_rejects_non_positive_user_id(self):
		url = reverse('follow-user')
		response = self.client.post(url, {'user_id': 0}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid follow payload')
		self.assertIn('user_id', response.data.get('errors', {}))

	def test_like_requires_post_id(self):
		url = reverse('like-post')
		response = self.client.post(url, {}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid like payload')
		self.assertIn('errors', response.data)

	def test_unlike_rejects_non_integer_post_id(self):
		url = reverse('unlike-post')
		response = self.client.post(url, {'post_id': 'abc'}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid unlike payload')
		self.assertIn('post_id', response.data.get('errors', {}))

	def test_comment_create_requires_post_and_content(self):
		url = reverse('comment-create')
		response = self.client.post(url, {'post': 1}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid comment payload')
		self.assertIn('errors', response.data)

	def test_comment_list_requires_post_id_query_param(self):
		url = reverse('comment-list')
		response = self.client.get(url)
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid comment query')
		self.assertIn('post_id', response.data.get('errors', {}))

	def test_profile_update_rejects_invalid_avatar_url(self):
		url = reverse('profile')
		response = self.client.put(url, {'avatar': 'not-a-url'}, format='json')
		self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
		self.assertEqual(response.data.get('detail'), 'invalid profile payload')
		self.assertIn('avatar', response.data.get('errors', {}))

	def test_follow_user_success(self):
		url = reverse('follow-user')
		response = self.client.post(url, {'user_id': self.other.id}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data.get('detail'), 'Now following')

	def test_like_post_success(self):
		post = Post.objects.create(user=self.other, content='hello')
		url = reverse('like-post')
		response = self.client.post(url, {'post_id': post.id}, format='json')
		self.assertEqual(response.status_code, status.HTTP_201_CREATED)
		self.assertEqual(response.data.get('detail'), 'Post liked')


class QueryOptimizationTests(APITestCase):
	def setUp(self):
		self.viewer = User.objects.create_user(username='viewer', password='viewer-pass')
		self.author1 = User.objects.create_user(username='author1', password='author-pass')
		self.author2 = User.objects.create_user(username='author2', password='author-pass')

		Follower.objects.create(user=self.viewer, follows=self.author1)
		Follower.objects.create(user=self.viewer, follows=self.author2)

		for i in range(3):
			Post.objects.create(user=self.author1, content=f'a1-post-{i}')
			Post.objects.create(user=self.author2, content=f'a2-post-{i}')

	def test_get_feed_avoids_n_plus_one_on_post_user(self):
		queryset = get_feed(self.viewer)
		with self.assertNumQueries(1):
			for post in queryset:
				_ = post.user.username

	def test_get_followers_avoids_n_plus_one_on_related_users(self):
		queryset = get_followers(self.author1)
		with self.assertNumQueries(1):
			for follower in queryset:
				_ = follower.user.username
				_ = follower.follows.username

	def test_get_following_avoids_n_plus_one_on_related_users(self):
		queryset = get_following(self.viewer)
		with self.assertNumQueries(1):
			for following in queryset:
				_ = following.user.username
				_ = following.follows.username


class RateLimitMiddlewareTests(APITestCase):
	def setUp(self):
		os.environ["RATE_LIMIT_USE_REDIS"] = "0"
		reset_rate_limiter()
		reset_cache_client()

	def tearDown(self):
		reset_rate_limiter()
		reset_cache_client()
		os.environ.pop("USER_SENSITIVE_RATE_LIMIT", None)
		os.environ.pop("USER_SENSITIVE_RATE_WINDOW_SECONDS", None)
		os.environ.pop("USER_AUTH_RATE_LIMIT", None)
		os.environ.pop("USER_AUTH_RATE_WINDOW_SECONDS", None)

	def test_sensitive_endpoint_rate_limited(self):
		user = User.objects.create_user(username='rate-user', password='rate-pass')
		other = User.objects.create_user(username='rate-other', password='rate-pass')
		self.client.force_authenticate(user=user)

		os.environ["USER_SENSITIVE_RATE_LIMIT"] = "1"
		os.environ["USER_SENSITIVE_RATE_WINDOW_SECONDS"] = "60"

		url = reverse('follow-user')
		first = self.client.post(url, {'user_id': other.id}, format='json')
		second = self.client.post(url, {'user_id': other.id}, format='json')

		self.assertEqual(first.status_code, status.HTTP_201_CREATED)
		self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
		self.assertEqual(second.json().get('detail'), 'Rate limit exceeded')

	def test_auth_endpoint_rate_limited(self):
		User.objects.create_user(username='auth-user', password='auth-pass')
		os.environ["USER_AUTH_RATE_LIMIT"] = "1"
		os.environ["USER_AUTH_RATE_WINDOW_SECONDS"] = "60"

		url = reverse('token_obtain_pair')
		payload = {'username': 'auth-user', 'password': 'auth-pass'}

		first = self.client.post(url, payload, format='json')
		second = self.client.post(url, payload, format='json')

		self.assertEqual(first.status_code, status.HTTP_200_OK)
		self.assertEqual(second.status_code, status.HTTP_429_TOO_MANY_REQUESTS)
		self.assertEqual(second.json().get('detail'), 'Rate limit exceeded')


class FeedCacheTests(APITestCase):
	def setUp(self):
		os.environ["CACHE_USE_REDIS"] = "0"
		os.environ["USER_FEED_CACHE_TTL"] = "120"
		reset_cache_client()

		self.viewer = User.objects.create_user(username='cache-viewer', password='viewer-pass')
		self.author = User.objects.create_user(username='cache-author', password='author-pass')
		Follower.objects.create(user=self.viewer, follows=self.author)
		Post.objects.create(user=self.author, content='cached-post')

		self.client.force_authenticate(user=self.viewer)

	def tearDown(self):
		reset_cache_client()
		os.environ.pop("USER_FEED_CACHE_TTL", None)

	def test_feed_endpoint_returns_cache_hit_on_second_request(self):
		url = reverse('feed')

		first = self.client.get(url)
		second = self.client.get(url)

		self.assertEqual(first.status_code, status.HTTP_200_OK)
		self.assertEqual(second.status_code, status.HTTP_200_OK)
		self.assertEqual(first["X-Cache"], "MISS")
		self.assertEqual(second["X-Cache"], "HIT")
		self.assertEqual(first.json(), second.json())

	def test_feed_cache_invalidated_after_follow_action(self):
		feed_url = reverse('feed')
		follow_url = reverse('follow-user')

		target = User.objects.create_user(username='new-target', password='target-pass')
		Post.objects.create(user=target, content='new-target-post')

		seed = self.client.get(feed_url)
		cached = self.client.get(feed_url)
		self.assertEqual(seed["X-Cache"], "MISS")
		self.assertEqual(cached["X-Cache"], "HIT")

		follow_response = self.client.post(follow_url, {'user_id': target.id}, format='json')
		self.assertEqual(follow_response.status_code, status.HTTP_201_CREATED)

		after_invalidation = self.client.get(feed_url)
		self.assertEqual(after_invalidation["X-Cache"], "MISS")
		contents = [post["content"] for post in after_invalidation.json()]
		self.assertIn('new-target-post', contents)
