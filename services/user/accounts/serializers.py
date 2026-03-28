from django.contrib.auth.models import User
from rest_framework import serializers

from .models import Comment, Follower, Like, Post, Profile
from .service import create_user_with_profile


class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ("username", "password", "email")
        extra_kwargs = {"password": {"write_only": True}}

    def create(self, validated_data):
        return create_user_with_profile(
            username=validated_data["username"],
            password=validated_data["password"],
            email=validated_data.get("email", ""),
        )

    def validate_username(self, value: str) -> str:
        username = value.strip()
        if not username:
            raise serializers.ValidationError("Username cannot be blank")
        return username

    def validate_password(self, value: str) -> str:
        if len(value) < 8:
            raise serializers.ValidationError("Password must be at least 8 characters")
        return value


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ("bio", "avatar", "location", "created_at", "updated_at")
        read_only_fields = ("created_at", "updated_at")


class ProfileUpdatePayloadSerializer(serializers.Serializer):
    bio = serializers.CharField(required=False, allow_blank=True, trim_whitespace=True)
    avatar = serializers.URLField(required=False, allow_blank=True)
    location = serializers.CharField(
        required=False,
        allow_blank=True,
        trim_whitespace=True,
        max_length=100,
    )


class FollowerSerializer(serializers.ModelSerializer):
    class Meta:
        model = Follower
        fields = ("id", "user", "follows", "created_at")


class PostSerializer(serializers.ModelSerializer):
    class Meta:
        model = Post
        fields = ("id", "user", "content", "created_at", "updated_at")


class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ("id", "user", "post", "created_at")


class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ("id", "user", "post", "content", "created_at", "updated_at")


class UserIdPayloadSerializer(serializers.Serializer):
    user_id = serializers.IntegerField(min_value=1)


class PostIdPayloadSerializer(serializers.Serializer):
    post_id = serializers.IntegerField(min_value=1)


class CommentCreatePayloadSerializer(serializers.Serializer):
    post = serializers.IntegerField(min_value=1)
    content = serializers.CharField(allow_blank=False, trim_whitespace=True, max_length=1000)

    def validate_content(self, value: str) -> str:
        content = value.strip()
        if not content:
            raise serializers.ValidationError("Content cannot be blank")
        return content


class CommentListQuerySerializer(serializers.Serializer):
    post_id = serializers.IntegerField(min_value=1)