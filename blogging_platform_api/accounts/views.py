from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.authentication import TokenAuthentication
from django.db.models import Avg, Count
from django_filters import filters
from rest_framework import generics, permissions, serializers
from django.contrib.auth import get_user_model
from .serializers import RegisterSerializer, UserProfileSerializer, PostSerializer, CommentSerializer, SubscriptionSerializer
from rest_framework.permissions import IsAuthenticated
from .permissions import IsAuthorOrReadOnly
from .models import Post,Comment,PostRating
from rest_framework.pagination import PageNumberPagination
from .filters import PostFilter
from rest_framework import filters
from django.core.mail import send_mail
from django.shortcuts import get_object_or_404, render
from django.http import JsonResponse
from rest_framework.response import Response
from .models import Subscription
from rest_framework import serializers
from django.db.models import Q
from rest_framework.views import APIView,status
from allauth.account.models import EmailAddress
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from rest_framework.generics import GenericAPIView


User = get_user_model()

class RegisterView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    

    def get_object(self):
        return self.request.user
    
    def retrieve(self, request, *args, **kwargs):  

    # Retrieve the logged-in user's profile
        user = request.user
        serializer = self.get_serializer(user.profile)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        # Update the logged-in user's profile
        user = request.user
        serializer = self.get_serializer(user.profile, data=request.data, partial=True)
        serializer.is_valid(raise_exception=True)
        serializer.save() 
    
        return Response(serializer.data) 


class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostListCreateView(generics.ListCreateAPIView):
    queryset = Post.objects.filter(status='published').order_by('-published_date')
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly,IsAuthorOrReadOnly]
    authentication_classes = [TokenAuthentication]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'tags__name', 'author__username']  # Search by title, content, tags, and author
    ordering_fields = ['published_date', 'category']
    ordering = ['-published_date']
    search_fields = ['title', 'content']

    def perform_create(self, serializer):
        # Ensure content is passed and not empty
        content = self.request.data.get('content')
        if not content:
            raise serializers.ValidationError("Content cannot be empty.")
        serializer.save(author=self.request.user, status='draft', content=content)

class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    authentication_classes = [TokenAuthentication]

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        else:
            self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return super().get_permissions()


    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Ensure content is passed and not empty when updating
        if 'content' in request.data and not request.data['content']:
            return Response({'error': 'Content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        return Response(serializer.data)

    def get_object(self):
        try:
            return Post.objects.get(pk=self.kwargs.get('pk'))
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)
        


from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from rest_framework.permissions import IsAuthenticated
from .permissions import IsOwner



class PostDeleteView(LoginRequiredMixin, PermissionRequiredMixin, GenericAPIView):
    permission_classes = [IsAuthenticated, IsOwner]  # Only owner can delete

    def delete(self, request, *args, **kwargs):
        post = get_object_or_404(Post, pk=kwargs['pk'])
        if post.author != request.user:
            # Handle unauthorized access (e.g., return 403)
            return Response(status=status.HTTP_403_FORBIDDEN)
        post.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)



    
class LikePostView(generics.GenericAPIView):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        if user in post.likes.all():
            post.likes.remove(user)
        else:
            post.likes.add(user)
        return Response({'message': 'Post liked/unliked successfully.'})
    
class RatePostView(generics.GenericAPIView):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user = request.user
        rating = request.data.get('rating')
        if rating is None:
            return Response({'error': 'Rating is required.'}, status=400)
        try:
            rating = int(rating)
            if rating < 1 or rating > 5:
                return Response({'error': 'Rating must be between 1 and 5.'}, status=400)
        except ValueError:
            return Response({'error': 'Rating must be an integer.'}, status=400)
        existing_rating = PostRating.objects.filter(post=post, user=user).first()
        if existing_rating:
            existing_rating.rating = rating
            existing_rating.save()
        else:
            PostRating.objects.create(post=post, user=user, rating=rating)
        return Response({'message': 'Post rated successfully.'})
    



class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer

    def perform_create(self, serializer):
        serializer.save(user=self.request.user, post=self.get_object())

class CommentUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    
    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if instance.parent_comment:
            instance.parent_comment.delete()
        return super().update(request, *args, **kwargs)
    
    def get_object(self):
        queryset = self.get_queryset()
        filter_kwargs = {'pk': self.kwargs['pk']}
        obj = queryset.filter(**filter_kwargs).first()
        if not obj:
            return Response(status=status.HTTP_404_NOT_FOUND)
        return obj

class TopRatedPostsView(generics.ListAPIView):
    queryset = Post.objects.annotate(avg_rating=Avg('postrating__rating')).order_by('-avg_rating')
    serializer_class = PostSerializer

class TopLikedPostsView(generics.ListAPIView):
    queryset = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count') 
    serializer_class = PostSerializer


class SharePostView(generics.GenericAPIView):
    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        recipient_email = request.data.get('recipient_email')
        # ... other sharing methods (e.g., social media)
        return Response({'message': 'Post shared successfully.'})



class SubscriptionView(generics.CreateAPIView):
    queryset = Subscription.objects.all()
    serializer_class = SubscriptionSerializer
    permission_classes = [permissions.IsAuthenticated] 


    def perform_create(self, serializer): 

    # Ensure user doesn't subscribe to themselves
        if serializer.validated_data['user'] == serializer.validated_data.get('author', None):
            raise serializers.ValidationError("You cannot subscribe to yourself.")
        serializer.save()

class UnsubscribeView(generics.DestroyAPIView):
    queryset = Subscription.objects.all()
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        pk = self.kwargs.get('pk')
        return self.get_queryset().filter(pk=pk, user=self.request.user).first()

def send_subscription_notification(user, post):
    subject = f"New post from {post.author.username}"
    message = f"There's a new post titled '{post.title}' by {post.author.username} in a category you're subscribed to. Check it out here: {post.get_absolute_url()}"
    send_mail(subject, message, '', [user.email])

class NewPostNotification(generics.GenericAPIView):
    

    def post(self, request):
        # This view should be triggered when a new post is created
        # You can use signals or schedule a task to call this view
        post_id = request.data.get('post_id')
        if post_id:
            try:
                post = get_object_or_404(Post, pk=post_id)
                # Get users subscribed to the post's author or category
                subscribers = Subscription.objects.filter(
                (Q(author=post.author) | Q(category=post.category)) & ~Q(user=post.author)
                )
                for subscriber in subscribers:
                    send_subscription_notification(subscriber.user, post)
                return Response({'message': 'Notifications sent successfully.'})
            except Exception as e:
                return Response({'error': str(e)}, status=500)
        else:
            return Response({'error': 'Missing post ID in request data.'}, status=400)
        
class MyProtectedView(APIView):  
    permission_classes = [IsAuthenticated]  # Requires user to be authenticated

    def get(self, request):
        # ... your view logic
        return Response(...)
    
def share_post_via_email(request, post_id, recipient_email):
    post = get_object_or_404(Post, pk=post_id)
    recipient = EmailAddress.objects.filter(email=recipient_email).first()  # Check for existing user

    # Craft your email content here (subject, message, etc.)
    subject = f"Check out this post: {post.title}"
    message = f"Your friend {request.user.username} shared a post with you:\n\n{post.get_absolute_url()}\n\n{post.content[:200]}..."  # Truncate content for preview

    if recipient:
        # Send email to existing user
        send_mail(subject, message, request.user.email, [recipient.email])
    else:
        # Send email to non-user (implement logic if desired)
        send_mail(subject, message, request.user.email, [recipient_email])

    return Response({'message': 'Post shared successfully.'})