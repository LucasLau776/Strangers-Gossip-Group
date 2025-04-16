from rest_framework import serializers # type: ignore
from .models import Confession, Like, Comment
from django.contrib.auth.models import User

class ConfessionSerializer(serializers.ModelSerializer):
    likes_count = serializers.IntegerField(source='likes.count', read_only=True)
    comments_count = serializers.IntegerField(source='comments.count', read_only=True)

    class Meta:
        model = Confession
        fields = ['id', 'content', 'created_at', 'likes_count', 'comments_count']

class LikeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Like
        fields = ['id', 'user', 'confession']

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'confession', 'content', 'created_at']
