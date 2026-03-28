"""
Service layer for user-related business logic.
Each function encapsulates business rules and DB operations, keeping views thin.
"""
from typing import Optional

from django.contrib.auth.models import User
from django.db import transaction
from django.db.models import QuerySet

from .models import Comment, Follower, Like, Post, Profile

# USER SERVICES

def create_user_with_profile(username: str, password: str, email: str = "") -> User:
    """Create a new user and associated profile."""
    with transaction.atomic():
        user = User.objects.create_user(username=username, password=password, email=email)
        Profile.objects.create(user=user)
    return user

def get_profile(user: User) -> Profile:
    """Return the profile for a user."""
    return user.profile

def update_profile(
    user: User,
    bio: Optional[str] = None,
    avatar: Optional[str] = None,
    location: Optional[str] = None,
) -> Profile:
    """Update profile fields for a user."""
    profile = user.profile
    if bio is not None:
        profile.bio = bio
    if avatar is not None:
        profile.avatar = avatar
    if location is not None:
        profile.location = location
    profile.save()
    return profile

# FOLLOW SERVICES

def follow_user(user: User, target_id: int) -> tuple[bool, str]:
    """Follow another user. Returns (created, message)."""
    if user.id == target_id:
        return False, "Cannot follow yourself"
    target = User.objects.filter(id=target_id).first()
    if not target:
        return False, "User not found"
    obj, created = Follower.objects.get_or_create(user=user, follows=target)
    if not created:
        return False, "Already following"
    return True, "Now following"

def unfollow_user(user: User, target_id: int) -> tuple[bool, str]:
    """Unfollow another user. Returns (deleted, message)."""
    target = User.objects.filter(id=target_id).first()
    if not target:
        return False, "User not found"
    deleted, _ = Follower.objects.filter(user=user, follows=target).delete()
    if deleted:
        return True, "Unfollowed"
    return False, "Not following"

# POST SERVICES

def get_feed(user: User) -> QuerySet[Post]:
    """Return posts from users this user follows."""
    following_ids = user.following.values_list('follows_id', flat=True)
    return (
        Post.objects.filter(user__id__in=following_ids)
        .select_related('user')
        .order_by('-created_at')
    )

# LIKE SERVICES

def like_post(user: User, post_id: int) -> tuple[bool, str]:
    """Like a post. Returns (created, message)."""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return False, "Post not found"
    obj, created = Like.objects.get_or_create(user=user, post=post)
    if not created:
        return False, "Already liked"
    return True, "Post liked"

def unlike_post(user: User, post_id: int) -> tuple[bool, str]:
    """Unlike a post. Returns (deleted, message)."""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return False, "Post not found"
    deleted, _ = Like.objects.filter(user=user, post=post).delete()
    if deleted:
        return True, "Unliked"
    return False, "Not liked"

# COMMENT SERVICES

def add_comment(user: User, post_id: int, content: str) -> tuple[Optional[Comment], str]:
    """Add a comment to a post."""
    try:
        post = Post.objects.get(id=post_id)
    except Post.DoesNotExist:
        return None, "Post not found"
    comment = Comment.objects.create(user=user, post=post, content=content)
    return comment, "Comment added"

def get_comments(post_id: int) -> QuerySet[Comment]:
    """Return comments for a post."""
    return (
        Comment.objects.filter(post_id=post_id)
        .select_related('user', 'post')
        .order_by('created_at')
    )


def get_followers(user: User) -> QuerySet[Follower]:
    """Return users following the given user."""
    return Follower.objects.filter(follows=user).select_related('user', 'follows')


def get_following(user: User) -> QuerySet[Follower]:
    """Return users that the given user follows."""
    return Follower.objects.filter(user=user).select_related('user', 'follows')
