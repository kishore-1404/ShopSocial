from django.urls import path
from .views import RegisterView, ProfileView, FollowUserView, UnfollowUserView, FollowersListView, FollowingListView, FeedView, LikePostView, UnlikePostView, CommentCreateView, CommentListView

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('follow/', FollowUserView.as_view(), name='follow-user'),
    path('unfollow/', UnfollowUserView.as_view(), name='unfollow-user'),
    path('followers/', FollowersListView.as_view(), name='followers-list'),
    path('following/', FollowingListView.as_view(), name='following-list'),
    path('feed/', FeedView.as_view(), name='feed'),
    path('like/', LikePostView.as_view(), name='like-post'),
    path('unlike/', UnlikePostView.as_view(), name='unlike-post'),
    path('comments/', CommentListView.as_view(), name='comment-list'),
    path('comments/create/', CommentCreateView.as_view(), name='comment-create'),
]
