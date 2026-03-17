
from rest_framework import permissions, status, generics, views
from rest_framework.response import Response
from django.contrib.auth.models import User
from rest_framework.serializers import ModelSerializer, Serializer, IntegerField
from rest_framework.permissions import AllowAny, IsAuthenticated
from .models import Profile, Follower, Post, Like, Comment

class CommentSerializer(ModelSerializer):
	class Meta:
		model = Comment
		fields = ('id', 'user', 'post', 'content', 'created_at', 'updated_at')

class CommentCreateView(generics.CreateAPIView):
	serializer_class = CommentSerializer
	permission_classes = [IsAuthenticated]

	def perform_create(self, serializer):
		serializer.save(user=self.request.user)

class CommentListView(generics.ListAPIView):
	serializer_class = CommentSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		post_id = self.request.query_params.get('post_id')
		if not post_id:
			return Comment.objects.none()
		return Comment.objects.filter(post_id=post_id).order_by('created_at')

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
		try:
			post = Post.objects.get(id=post_id)
		except Post.DoesNotExist:
			return Response({'detail': 'Post not found'}, status=404)
		obj, created = Like.objects.get_or_create(user=request.user, post=post)
		if not created:
			return Response({'detail': 'Already liked'}, status=400)
		return Response({'detail': 'Post liked'}, status=201)

class UnlikePostView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		post_id = request.data.get('post_id')
		if not post_id:
			return Response({'detail': 'post_id required'}, status=400)
		try:
			post = Post.objects.get(id=post_id)
		except Post.DoesNotExist:
			return Response({'detail': 'Post not found'}, status=404)
		deleted, _ = Like.objects.filter(user=request.user, post=post).delete()
		if deleted:
			return Response({'detail': 'Unliked'}, status=200)
		return Response({'detail': 'Not liked'}, status=400)

class PostSerializer(ModelSerializer):
	class Meta:
		model = Post
		fields = ('id', 'user', 'content', 'created_at', 'updated_at')

class FeedView(generics.ListAPIView):
	serializer_class = PostSerializer
	permission_classes = [IsAuthenticated]

	def get_queryset(self):
		user = self.request.user
		following_ids = user.following.values_list('follows_id', flat=True)
		return Post.objects.filter(user__id__in=following_ids).order_by('-created_at')

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
		if int(target_id) == request.user.id:
			return Response({'detail': 'Cannot follow yourself'}, status=400)
		target = User.objects.filter(id=target_id).first()
		if not target:
			return Response({'detail': 'User not found'}, status=404)
		obj, created = Follower.objects.get_or_create(user=request.user, follows=target)
		if not created:
			return Response({'detail': 'Already following'}, status=400)
		return Response({'detail': 'Now following'}, status=201)

class UnfollowUserView(views.APIView):
	permission_classes = [IsAuthenticated]

	def post(self, request):
		target_id = request.data.get('user_id')
		if not target_id:
			return Response({'detail': 'user_id required'}, status=400)
		target = User.objects.filter(id=target_id).first()
		if not target:
			return Response({'detail': 'User not found'}, status=404)
		deleted, _ = Follower.objects.filter(user=request.user, follows=target).delete()
		if deleted:
			return Response({'detail': 'Unfollowed'}, status=200)
		return Response({'detail': 'Not following'}, status=400)

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
		user = User.objects.create_user(
			username=validated_data['username'],
			password=validated_data['password'],
			email=validated_data.get('email', '')
		)
		Profile.objects.create(user=user)  # Create profile on registration
		return user

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

class ProfileView(generics.RetrieveUpdateAPIView):
	serializer_class = ProfileSerializer
	permission_classes = [IsAuthenticated]

	def get_object(self):
		return self.request.user.profile
