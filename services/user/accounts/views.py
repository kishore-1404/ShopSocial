import os

from django.contrib.auth.models import User
from rest_framework import generics, status, views
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from common.cache_service import get_cache_client

from .serializers import (
	CommentCreatePayloadSerializer,
	CommentListQuerySerializer,
	CommentSerializer,
	FollowerSerializer,
	PostIdPayloadSerializer,
	PostSerializer,
	ProfileSerializer,
	ProfileUpdatePayloadSerializer,
	RegisterSerializer,
	UserIdPayloadSerializer,
)
from .service import (
	add_comment,
	follow_user,
	get_comments,
	get_feed,
	get_followers,
	get_following,
	get_profile,
	like_post,
	unfollow_user,
	unlike_post,
	update_profile,
)


cache_client = get_cache_client()


def _feed_cache_ttl() -> int:
	try:
		value = int(os.environ.get("USER_FEED_CACHE_TTL", "30"))
		return value if value > 0 else 30
	except ValueError:
		return 30


def _feed_cache_key(user_id: int) -> str:
	return f"user:feed:{user_id}"


def _invalidate_feed_cache(user_id: int) -> None:
	cache_client.delete(_feed_cache_key(user_id))


class RegisterView(generics.CreateAPIView):
	queryset = User.objects.all()
	serializer_class = RegisterSerializer
	permission_classes = [AllowAny]

	def create(self, request, *args, **kwargs):
		serializer = self.get_serializer(data=request.data)
		serializer.is_valid(raise_exception=True)
		self.perform_create(serializer)
		headers = self.get_success_headers(serializer.data)

		response_data = dict(serializer.data)
		if serializer.instance is not None:
			response_data["id"] = serializer.instance.id
		return Response(response_data, status=status.HTTP_201_CREATED, headers=headers)


def _validation_error_response(serializer, default_detail: str) -> Response:
	"""Return a uniform validation error shape across payload/query serializers."""
	return Response(
		{"detail": default_detail, "errors": serializer.errors},
		status=status.HTTP_400_BAD_REQUEST,
	)


class ProfileView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		profile = get_profile(request.user)
		return Response(ProfileSerializer(profile).data)

	def put(self, request):
		payload = ProfileUpdatePayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid profile payload")

		updated_profile = update_profile(
			request.user,
			bio=payload.validated_data.get("bio"),
			avatar=payload.validated_data.get("avatar"),
			location=payload.validated_data.get("location"),
		)
		return Response(ProfileSerializer(updated_profile).data)


class FollowUserView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		payload = UserIdPayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid follow payload")

		created, message = follow_user(request.user, payload.validated_data["user_id"])
		status_code = (
			status.HTTP_201_CREATED
			if created
			else status.HTTP_400_BAD_REQUEST
			if message in ("Already following", "Cannot follow yourself")
			else status.HTTP_404_NOT_FOUND
		)
		_invalidate_feed_cache(request.user.id)
		return Response({"detail": message}, status=status_code)


class UnfollowUserView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		payload = UserIdPayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid unfollow payload")

		deleted, message = unfollow_user(request.user, payload.validated_data["user_id"])
		status_code = (
			status.HTTP_200_OK
			if deleted
			else status.HTTP_400_BAD_REQUEST
			if message == "Not following"
			else status.HTTP_404_NOT_FOUND
		)
		_invalidate_feed_cache(request.user.id)
		return Response({"detail": message}, status=status_code)


class FollowersListView(generics.ListAPIView):
	serializer_class = FollowerSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return get_followers(self.request.user)


class FollowingListView(generics.ListAPIView):
	serializer_class = FollowerSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return get_following(self.request.user)


class FeedView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		cached_feed = cache_client.get_json(_feed_cache_key(request.user.id))
		if isinstance(cached_feed, list):
			response = Response(cached_feed)
			response["X-Cache"] = "HIT"
			return response

		posts = get_feed(request.user)
		serialized_posts = PostSerializer(posts, many=True).data
		cache_client.set_json(_feed_cache_key(request.user.id), serialized_posts, _feed_cache_ttl())

		response = Response(serialized_posts)
		response["X-Cache"] = "MISS"
		return response


class LikePostView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		payload = PostIdPayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid like payload")

		created, message = like_post(request.user, payload.validated_data["post_id"])
		status_code = (
			status.HTTP_201_CREATED
			if created
			else status.HTTP_400_BAD_REQUEST
			if message == "Already liked"
			else status.HTTP_404_NOT_FOUND
		)
		_invalidate_feed_cache(request.user.id)
		return Response({"detail": message}, status=status_code)


class UnlikePostView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		payload = PostIdPayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid unlike payload")

		deleted, message = unlike_post(request.user, payload.validated_data["post_id"])
		status_code = (
			status.HTTP_200_OK
			if deleted
			else status.HTTP_400_BAD_REQUEST
			if message == "Not liked"
			else status.HTTP_404_NOT_FOUND
		)
		_invalidate_feed_cache(request.user.id)
		return Response({"detail": message}, status=status_code)


class CommentCreateView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		payload = CommentCreatePayloadSerializer(data=request.data)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid comment payload")

		comment, message = add_comment(
			request.user,
			payload.validated_data["post"],
			payload.validated_data["content"],
		)
		if comment is None:
			return Response({"detail": message}, status=status.HTTP_404_NOT_FOUND)

		_invalidate_feed_cache(request.user.id)
		return Response(CommentSerializer(comment).data, status=status.HTTP_201_CREATED)


class CommentListView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		payload = CommentListQuerySerializer(data=request.query_params)
		if not payload.is_valid():
			return _validation_error_response(payload, "invalid comment query")

		comments = get_comments(payload.validated_data["post_id"])
		return Response(CommentSerializer(comments, many=True).data)
