
from rest_framework import permissions, status, generics, views
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer, Serializer, IntegerField
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Profile, Follower, Post, Like, Comment
from .service import (
	create_user_with_profile, get_profile, update_profile,
	follow_user, unfollow_user, get_feed,
	like_post, unlike_post, add_comment, get_comments
)

class CommentSerializer(ModelSerializer):
	class Meta:
		model = Comment
		fields = ('id', 'user', 'post', 'content', 'created_at', 'updated_at')

class CommentCreateView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		post_id = request.data.get('post')
		content = request.data.get('content')
		if not post_id or not content:
			return Response({'detail': 'post and content required'}, status=400)
		comment, msg = add_comment(request.user, post_id, content)
		if not comment:
			return Response({'detail': msg}, status=404)
		return Response(CommentSerializer(comment).data, status=201)

class CommentListView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		post_id = request.query_params.get('post_id')
		if not post_id:
			return Response({'detail': 'post_id required'}, status=400)
		comments = get_comments(post_id)
		return Response(CommentSerializer(comments, many=True).data)

class LikeSerializer(ModelSerializer):
	class Meta:
		model = Like
		fields = ('id', 'user', 'post', 'created_at')

class LikePostView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		post_id = request.data.get('post_id')
		if not post_id:
			return Response({'detail': 'post_id required'}, status=400)
		created, msg = like_post(request.user, post_id)
		status_code = 201 if created else 400 if msg == 'Already liked' else 404
		return Response({'detail': msg}, status=status_code)

class UnlikePostView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		post_id = request.data.get('post_id')
		if not post_id:
			return Response({'detail': 'post_id required'}, status=400)
		deleted, msg = unlike_post(request.user, post_id)
		status_code = 200 if deleted else 400 if msg == 'Not liked' else 404
		return Response({'detail': msg}, status=status_code)

class PostSerializer(ModelSerializer):
	class Meta:
		model = Post
		fields = ('id', 'user', 'content', 'created_at', 'updated_at')

class FeedView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		posts = get_feed(request.user)
		return Response(PostSerializer(posts, many=True).data)

# ...existing RegisterSerializer, RegisterView, ProfileSerializer, ProfileView...

class FollowerSerializer(ModelSerializer):
	class Meta:
		model = Follower
		fields = ('id', 'user', 'follows', 'created_at')

class FollowUserSerializer(Serializer):
	user_id = IntegerField()

class FollowUserView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		target_id = request.data.get('user_id')
		if not target_id:
			return Response({'detail': 'user_id required'}, status=400)
		created, msg = follow_user(request.user, int(target_id))
		status_code = 201 if created else 400 if msg == 'Already following' or msg == 'Cannot follow yourself' else 404
		return Response({'detail': msg}, status=status_code)

class UnfollowUserView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		target_id = request.data.get('user_id')
		if not target_id:
			return Response({'detail': 'user_id required'}, status=400)
		deleted, msg = unfollow_user(request.user, int(target_id))
		status_code = 200 if deleted else 400 if msg == 'Not following' else 404
		return Response({'detail': msg}, status=status_code)

class FollowersListView(generics.ListAPIView):
	serializer_class = FollowerSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return Follower.objects.filter(follows=self.request.user)

class FollowingListView(generics.ListAPIView):
	serializer_class = FollowerSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		return Follower.objects.filter(user=self.request.user)
from rest_framework import generics, status
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.serializers import ModelSerializer
from .models import Profile

class RegisterSerializer(ModelSerializer):
	class Meta:
		model = User
		fields = ('username', 'password', 'email')
		extra_kwargs = {'password': {'write_only': True}}

	def create(self, validated_data):
		return create_user_with_profile(
			username=validated_data['username'],
			password=validated_data['password'],
			email=validated_data.get('email', '')
		)

class RegisterView(generics.CreateAPIView):
	queryset = User.objects.all()
	serializer_class = RegisterSerializer
	permission_classes = [AllowAny]

	def create(self, request, *args, **kwargs):
		response = super().create(request, *args, **kwargs)
		# Add user id to response if registration succeeded
		if response.status_code == 201:
			user = User.objects.get(username=request.data['username'])
			response.data['id'] = user.id
		return response

class ProfileSerializer(ModelSerializer):
	class Meta:
		model = Profile
		fields = ('bio', 'avatar', 'location', 'created_at', 'updated_at')

class ProfileView(views.APIView):
	permission_classes = [IsAuthenticated]

	def get(self, request):
		profile = get_profile(request.user)
		return Response(ProfileSerializer(profile).data)

	def put(self, request):
		data = request.data
		profile = update_profile(
			request.user,
			bio=data.get('bio'),
			avatar=data.get('avatar'),
			location=data.get('location')
		)
		return Response(ProfileSerializer(profile).data)
