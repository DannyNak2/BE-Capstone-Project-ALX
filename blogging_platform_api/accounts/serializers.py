from rest_framework.serializers import ModelSerializer
from django.contrib.auth.password_validation import validate_password
from rest_framework import serializers
from django.contrib.auth import get_user_model
from rest_framework_simplejwt.tokens import RefreshToken
from .models import Post, Category, Tag, Comment,Subscription,Profile,PostLike 
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


class PostSerializer(serializers.ModelSerializer):
    likes_count = serializers.SerializerMethodField()
    average_rating = serializers.SerializerMethodField()
    category = serializers.PrimaryKeyRelatedField(queryset=Category.objects.all())
    tags = serializers.PrimaryKeyRelatedField(many=True, queryset=Tag.objects.all())
    author = serializers.CharField(source='author.username', read_only=True)  # Use the username
    category_name = serializers.SerializerMethodField()
    tags_names = serializers.SerializerMethodField()
    comments = serializers.SerializerMethodField()
    

    class Meta:
        model = Post
        fields = ['id', 'title', 'content', 'author', 'category', 'category_name', 'tags', 'tags_names', 'published_date', 'created_at', 'average_rating', 'likes_count', 'status', 'comments']
        read_only_fields = ['author', 'created_at']
        extra_kwargs = {
            'title': {'required': True},  # Set required as needed
            'content': {'required': True},  # Set required as needed
            'category': {'required': True},  # Set required as needed
            'tags': {'required': False}  # Adjust as needed
        }

    def to_representation(self, instance):
        """
        Customize the representation of the category and tags fields.
        """
        representation = super().to_representation(instance)
        
        # Override category to show its name instead of ID
        if instance.category:
            representation['category'] = instance.category.name
        else:
            representation['category'] = None
        
        # Override tags to show their names instead of IDs
        if instance.tags.exists():
            representation['tags'] = [tag.name for tag in instance.tags.all()]
        else:
            representation['tags'] = []
        
        return representation
    
    def get_comments(self, obj):
        # Get the comments for the post (only top-level comments)
        comments = Comment.objects.filter(post=obj, parent_comment__isnull=True).order_by('-created_at')
        return CommentSerializer(comments, many=True).data
    
    def get_category_name(self, obj):
        # Return the name of the category
        return obj.category.name if obj.category else None

    def get_tags_names(self, obj):
        # Return a list of tag names
        return [tag.name for tag in obj.tags.all()] if obj.tags.exists() else [] 

    def get_likes_count(self, obj):
        return PostLike.objects.filter(post=obj).count()  # Count likes for each post

    def get_average_rating(self, obj):
        ratings = obj.postrating_set.all()
        if ratings:
            return ratings.aggregate(Avg('rating'))['rating__avg']
        else:
            return None

    def create(self, validated_data):
        request = self.context.get('request')
        validated_data['author'] = request.user
        return super().create(validated_data)

    def validate(self, data):
        errors = {}
        
        # Ensure the title is provided
        if not data.get('title'):
            errors['title'] = "Title is required."
        
        # Ensure the content is provided
        if not data.get('content'):
            errors['content'] = "Content is required."
        
        # Ensure the category is provided
        if not data.get('category'):
            errors['category'] = "Category is required."

        # Ensure at least one tag is provided
        if 'tags' not in data or not data['tags']:
            errors['tags'] = "At least one tag is required."

        # If any errors have been found, raise a validation error with all messages
        if errors:
            raise serializers.ValidationError(errors)

        return data




class PostDeleteSerializer(serializers.Serializer):
    post_id = serializers.PrimaryKeyRelatedField(queryset=Post.objects.all())

class CommentSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()  # Shows the username instead of user ID
    replies = serializers.SerializerMethodField()  # Nested replies
    created_at = serializers.DateTimeField(format="%Y-%m-%d %H:%M:%S", read_only=True)

    class Meta:
        model = Comment
        fields = ['id', 'user', 'post', 'content', 'created_at', 'parent_comment', 'replies']
        read_only_fields = ['id', 'user', 'post', 'created_at']

    def get_replies(self, obj):
        if obj.replies.exists():
            return CommentSerializer(obj.replies.all(), many=True).data
        return []


class CreateCommentSerializer(serializers.ModelSerializer):
    parent_comment_id = serializers.IntegerField(required=False, allow_null=True)

    class Meta:
        model = Comment
        fields = ['id', 'post', 'content', 'parent_comment_id']

    def create(self, validated_data):
        parent_comment_id = validated_data.pop('parent_comment_id', None)
        comment = Comment.objects.create(**validated_data)
        if parent_comment_id:
            try:
                parent_comment = Comment.objects.get(id=parent_comment_id)
                comment.parent_comment = parent_comment
                comment.save()
            except Comment.DoesNotExist:
                raise serializers.ValidationError("Parent comment not found.")
        return comment

class RatePostSerializer(serializers.Serializer):
    rating = serializers.IntegerField(
        min_value=1,
        max_value=5,
        error_messages={
            'invalid': 'Rating must be an integer.',
            'min_value': 'Rating must be between 1 and 5.',
            'max_value': 'Rating must be between 1 and 5.',
        }
    )

class LikePostSerializer(serializers.Serializer):
    message = serializers.CharField(read_only=True)  # Dummy field just for compliance

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

class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['bio', 'profile_picture']

class UserProfileSerializer(serializers.ModelSerializer):
    profile = ProfileSerializer()  # Nested profile serializer
    authored_posts = PostSerializer(many=True, read_only=True)  # Showcase their posts


    class Meta:
        model = User
        fields = ['id', 'email', 'username', 'first_name', 'last_name', 'profile','authored_posts']

    def update(self, instance, validated_data):
        # Update the user instance
        profile_data = validated_data.pop('profile', None)
        if profile_data:
            profile = instance.profile
            profile.bio = profile_data.get('bio', profile.bio)
            profile.profile_picture = profile_data.get('profile_picture', profile.profile_picture)
            profile.save()
        
        # Update user fields
        instance.username = validated_data.get('username', instance.username)
        instance.first_name = validated_data.get('first_name', instance.first_name)
        instance.last_name = validated_data.get('last_name', instance.last_name)
        instance.save()
        return instance

class EmptySerializer(serializers.Serializer):
    pass