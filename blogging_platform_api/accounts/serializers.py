from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, Category, Tag, Comment,Subscription
from django.db.models import Q
from markdown2 import Markdown
import markdown2
from django.db.models import Avg, Count

User = get_user_model()

class RegisterSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['email', 'username', 'password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        # Apply Django's built-in password validators, including length validation
        validate_password(value)
        return value

    def create(self, validated_data):
        user = User.objects.create_user(
            email=validated_data['email'],
            username=validated_data['username'],
            password=validated_data['password']
        )
        return user

class UserProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'email', 'username']


class PostSerializer(serializers.ModelSerializer):
    content = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'category', 'tags', 'published_date', 'created_at', 'average_rating', 'likes_count']  # Added 'average_rating'
        read_only_fields = ['author', 'created_at']

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_average_rating(self, obj):
        ratings = obj.postrating_set.all()
        if ratings:
            return ratings.aggregate(Avg('rating'))['rating__avg']
        else:
            return None

    def get_content(self, obj):
        return markdown2.markdown(obj.content)

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)
    
    def validate_content(self, value):
        if len(value) > self.MAX_CONTENT_LENGTH:
            raise serializers.ValidationError(f"Content cannot exceed {self.MAX_CONTENT_LENGTH} characters.")
        return value

""" def validate(self, data):
        
        Ensure that movie_title and review_content are provided.

        if not data.get('title'):
            raise serializers.ValidationError("Post Title is required.")
        if not data.get('author'):
            raise serializers.ValidationError("Post Author is required.")
        return data """

class PostDeleteSerializer(serializers.Serializer):
    post_id = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

class CommentSerializer(serializers.ModelSerializer):
    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at']

    replies = serializers.SerializerMethodField()

    def get_replies(self, obj):
        return CommentSerializer(obj.get_children(), many=True).data



class CreateCommentSerializer(serializers.ModelSerializer):

    parent_comment_id = serializers.IntegerField(required=False)

    def create(self, validated_data):
        parent_comment_id = validated_data.pop('parent_comment_id', None)
        comment = super().create(validated_data)
        if parent_comment_id:
            parent_comment = Comment.objects.get(id=parent_comment_id)
            comment.parent_comment = parent_comment
            comment.save()
        return comment



class SubscriptionSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subscription
        fields = ['user', 'author', 'category']

    def validate(self, data):
        # Ensure user doesn't subscribe to themselves
        if data.get('author') == self.context['request'].user:
            raise serializers.ValidationError("You cannot subscribe to yourself.")
        return data

    def create(self, validated_data):
        # Check if the user is already subscribed to the same author or category
        existing_subscription = Subscription.objects.filter(
            user=validated_data['user']
        ).filter(
            Q(author=validated_data['author']) | Q(category=validated_data['category'])
        ).first()

        if existing_subscription:
            raise serializers.ValidationError("You are already subscribed to this author or category.")

        return super().create(validated_data)
