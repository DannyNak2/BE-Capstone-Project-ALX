# Django and third-party imports
from django.contrib import messages
from django.contrib.auth import get_user_model, authenticate, login
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.core.mail import send_mail
from django.db.models import Avg, Count, Q, Prefetch
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, render, redirect
from django.urls import reverse_lazy,reverse
from django.utils import timezone
from django.conf import settings  # Access email configuration if needed
from django.views.generic import CreateView

# Django REST Framework imports
from rest_framework import filters, generics, permissions, serializers, status
from rest_framework.authentication import TokenAuthentication
from rest_framework.generics import GenericAPIView
from rest_framework.pagination import PageNumberPagination
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken

# Django Filters imports
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework import filters


# Allauth imports
from allauth.account.models import EmailAddress

# Local app imports (models, serializers, permissions, filters)
from .models import Post, Comment, PostRating, Subscription, Category, Tag, PostLike
from .serializers import (
    RegisterSerializer, UserProfileSerializer, 
    PostSerializer, CommentSerializer, SubscriptionSerializer, RatePostSerializer, LikePostSerializer, EmptySerializer
)
from .permissions import IsAuthorOrReadOnly, IsOwner
from .filters import PostFilter



User = get_user_model()

class RegisterView(generics.CreateAPIView):
    template_name = 'register.html'
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    success_url = reverse_lazy('accounts:post-list-create')

    def get(self, request, *args, **kwargs):
        serializer = self.get_serializer()
        return render(request, self.template_name, {'serializer': serializer})

    def post(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.POST)
        if serializer.is_valid():
            serializer.save()
            messages.success(request, "Registration successful. You can now log in.")
            return redirect(self.success_url)
        else:
            # If the form is invalid, pass errors to the template
            return render(request, self.template_name, {'serializer': serializer, 'errors': serializer.errors})
        
class CustomLoginView(TokenObtainPairView):
    template_name = 'login.html'

    def get(self, request, *args, **kwargs):
        return render(request, self.template_name)

    def post(self, request, *args, **kwargs):
        response = super().post(request, *args, **kwargs)
        if response.status_code == status.HTTP_200_OK:
            # Authenticate the user
            email = request.POST.get('email')
            password = request.POST.get('password')
            user = authenticate(request, email=email, password=password)
            
            if user is not None:
                login(request, user)  # Log the user into the session
                messages.success(request, "You have successfully logged in.")
                return redirect(reverse('accounts:post-list-create'))  # Adjust this to your actual homepage
            else:
                messages.error(request, "Authentication failed.")
        else:
            messages.error(request, "Invalid email or password.")
        
        return render(request, self.template_name)

class ProfileView(generics.RetrieveUpdateAPIView):
    queryset = User.objects.all()
    serializer_class = UserProfileSerializer
    permission_classes = [permissions.IsAuthenticated]
    template_name = 'profile.html'

    def get_object(self):
        return self.request.user  # Returns the currently authenticated user

    def get(self, request, *args, **kwargs):
        user = self.get_object()
        form = UserProfileSerializer(user).data  # Serialize user data
        context = {'form': form, 'user': user}
        return render(request, self.template_name, context)

    def post(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(
            user, 
            data=request.data, 
            partial=True
        )

        # Check if the form is valid
        if serializer.is_valid():
            # Handle profile image separately because it's a file
            profile_data = request.data.get('profile', {})
            
            if 'profile_picture' in request.FILES:
                profile_picture = request.FILES['profile_picture']
                user.profile.profile_picture = profile_picture  # Save new profile picture

            # Update bio
            bio = request.data.get('bio', None)
            if bio is not None:
                user.profile.bio = bio
            
            # Save the user and profile
            user.profile.save()
            serializer.save()
            
            # Debugging: Print statements to check values
            print(f"Updated User: {user.username}, Bio: {user.profile.bio}, Profile Picture: {user.profile.profile_picture}")

            # Pass updated form and user back to the template
            context = {'form': serializer.data, 'user': user}
            return render(request, self.template_name, context)
        
        # If form is invalid, return the form with error messages
        context = {'form': serializer.errors, 'user': user}
        return render(request, self.template_name, context)



class StandardResultsSetPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100

class PostListCreateView(generics.ListCreateAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    filterset_class = PostFilter
    search_fields = ['title', 'content', 'tags__name', 'author__username']
    ordering_fields = ['published_date', 'category']
    ordering = ['-published_date']

    def get_queryset(self):
        # Start with the base queryset of published posts
        queryset = Post.objects.filter(status='published').order_by('-published_date')

        # Apply search filter (title, content, tags, author)
        search_query = self.request.GET.get('search', None)
        if search_query:
            queryset = queryset.filter(
                Q(title__icontains=search_query) | 
                Q(content__icontains=search_query) |
                Q(tags__name__icontains=search_query) |
                Q(author__username__icontains=search_query)
            ).distinct()

        # Apply category filter
        category = self.request.GET.get('category', None)
        if category:
            queryset = queryset.filter(category__id=category)

        # Apply tags filter (multiple tags)
        tags = self.request.GET.getlist('tags', None)
        if tags:
            queryset = queryset.filter(tags__id__in=tags).distinct()

        return queryset

    def get(self, request, *args, **kwargs):
        # Get the list of published posts
        posts = self.get_queryset()

        # Fetch categories and tags for the dropdowns
        categories = Category.objects.all()  # Get all categories
        tags = Tag.objects.all()  # Get all tags

        # Serialize the posts to pass to the template
        serializer = self.serializer_class(posts, many=True)
        

        # Render the template with the serialized data
        return render(request, 'post_list.html', {
            'posts': serializer.data,
            'categories': categories,
            'tags': tags,
        })

    def perform_create(self, serializer):
        title = self.request.data.get('title')
        content = self.request.data.get('content')
        status = self.request.data.get('status', 'draft')
        category_id = self.request.data.get('category')  # Get category ID from request
        tags_ids = self.request.data.get('tags')  # Get tags IDs from request
        
        # Validate title and content
        if not title:
            raise serializers.ValidationError("Title cannot be empty.")
        if not content:
            raise serializers.ValidationError("Content cannot be empty.")
        if status not in ['draft', 'published']:
            raise serializers.ValidationError("Status must be either 'draft' or 'published'.")

        # Validate category and tags
        if category_id:
            try:
                category = Category.objects.get(pk=category_id)
            except Category.DoesNotExist:
                raise serializers.ValidationError("Invalid category ID.")

        # Create the post with the selected category and tags
        serializer.save(author=self.request.user, status=status, title=title, content=content, category=category)

        # Handle tags (assuming a ManyToMany relationship)
        if tags_ids:
            tags = Tag.objects.filter(pk__in=tags_ids)
            serializer.instance.tags.set(tags)  # Associate tags with the post
            
class PostRetrieveUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Post.objects.all()
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]
    template_name = 'post_detail.html'

    def get_permissions(self):
        if self.request.method in ['PUT', 'PATCH', 'DELETE']:
            self.permission_classes = [permissions.IsAuthenticated, IsAuthorOrReadOnly]
        else:
            self.permission_classes = [permissions.IsAuthenticatedOrReadOnly]
        return super().get_permissions()
    
    def get(self, request, *args, **kwargs):
        post = self.get_object()
        return render(request, self.template_name, {'post': post})

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', False)
        instance = self.get_object()

        # Ensure content is passed and not empty when updating
        if 'content' in request.data and not request.data['content']:
            return Response({'error': 'Content cannot be empty.'}, status=status.HTTP_400_BAD_REQUEST)

        # Validate and set the status
        if 'status' in request.data:
            status = request.data['status']
            if status not in ['draft', 'published']:
                return Response({'error': "Status must be either 'draft' or 'published'."}, status=status.HTTP_400_BAD_REQUEST)

        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        self.perform_update(serializer)

        # Redirect to the post list after successful update
        return redirect('accounts:post-list-create')

    def delete(self, request, *args, **kwargs):
        instance = self.get_object()
        self.perform_destroy(instance)
        # Redirect to the post list after successful deletion
        return redirect('accounts:post-list-create')

    def get_object(self):
        try:
            return Post.objects.get(pk=self.kwargs.get('pk'))
        except Post.DoesNotExist:
            return Response(status=status.HTTP_404_NOT_FOUND)

class DraftPostListView(generics.ListAPIView):
    serializer_class = PostSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Post.objects.filter(author=self.request.user, status='draft').order_by('-created_at')


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
    serializer_class = LikePostSerializer  # Use the dummy serializer
    permission_classes = [IsAuthenticated]

    def post(self, request, pk):
        post = get_object_or_404(Post, pk=pk)
        user = request.user

        # Use get_or_create to like the post
        like, created = PostLike.objects.get_or_create(post=post, user=user)

        if not created:
            return Response({'message': 'You already liked this post.'}, status=400)

        return Response({'message': 'Post liked successfully.'})

    
class RatePostView(generics.GenericAPIView):
    serializer_class = RatePostSerializer
    permission_classes = [IsAuthenticated]  # Require the user to be logged in

    def post(self, request, pk):
        # Validate the incoming rating data using the serializer
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            post = get_object_or_404(Post, pk=pk)
            user = request.user

            # Extract the validated rating value from the serializer
            rating = serializer.validated_data['rating']

            # Use get_or_create to rate the post, either creating or updating the rating
            existing_rating, created = PostRating.objects.get_or_create(
                post=post,
                user=user,
                defaults={'rating': rating}
            )

            if not created:
                # Update the existing rating
                existing_rating.rating = rating
                existing_rating.save()

            return Response({'message': 'Post rated successfully.'})
        else:
            # If the data is invalid, return the serializer errors
            return Response(serializer.errors, status=400)
    


class CommentListCreateView(generics.ListCreateAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]

    def get_queryset(self):
        # Fetch comments for a specific post
        post_id = self.kwargs['post_id']
        return Comment.objects.filter(post_id=post_id, parent_comment__isnull=True).order_by('-created_at')

    def perform_create(self, serializer):
        post = get_object_or_404(Post, pk=self.kwargs['post_id'])
        serializer.save(user=self.request.user, post=post)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['comments'] = self.get_queryset()  # Ensure comments are being passed
        return context

class CommentUpdateDestroyView(generics.RetrieveUpdateDestroyAPIView):
    queryset = Comment.objects.all()
    serializer_class = CommentSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsAuthorOrReadOnly]

    def get_object(self):
        comment_id = self.kwargs['comment_pk']
        return get_object_or_404(Comment, id=comment_id)

    def update(self, request, *args, **kwargs):
        comment = self.get_object()
        if comment.parent_comment:
            # If updating a reply
            parent_comment = comment.parent_comment
            comment.parent_comment = parent_comment
        return super().update(request, *args, **kwargs)


class TopRatedPostsView(generics.ListAPIView):
    queryset = Post.objects.annotate(avg_rating=Avg('postrating__rating')).order_by('-avg_rating')
    serializer_class = PostSerializer

class TopLikedPostsView(generics.ListAPIView):
    queryset = Post.objects.annotate(like_count=Count('likes')).order_by('-like_count') 
    serializer_class = PostSerializer



class SharePostView(generics.GenericAPIView):
    permission_classes = [permissions.IsAuthenticated]  # Ensure only authenticated users can share posts
    serializer_class = EmptySerializer  # Dummy serializer
    

    def post(self, request, pk):
        # Retrieve the post object
        post = get_object_or_404(Post, pk=pk)

        # Get recipient email from the request
        recipient_email = request.data.get('recipient_email')

        # Validate recipient email
        if not recipient_email:
            return Response({'recipient_email': 'Recipient email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        # Prepare email details
        subject = f"Check out this post: {post.title}"
        message = (
            f"Hello!\n\n"
            f"Your friend {request.user.username} has shared a post with you:\n\n"
            f"Title: {post.title}\n"
            f"Link: {post.get_absolute_url()}\n\n"
            f"Content Preview: {post.content[:200]}...\n\n"  # Preview of content
        )
        
        # Send email
        try:
            send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [recipient_email])
        except Exception as e:
            return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

        # Generate social media links
        social_media_links = {
            'facebook': f"https://www.facebook.com/sharer/sharer.php?u={post.get_absolute_url()}",
            'twitter': f"https://twitter.com/intent/tweet?text={post.title}&url={post.get_absolute_url()}",
        }

        # Return response
        return Response({
            'message': 'Post shared successfully via email.',
            'social_media_links': social_media_links
        })



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
        # Fetch the subscription either by author or category
        user = self.request.user
        author_id = self.request.data.get('author_id')
        category_id = self.request.data.get('category_id')

        # Look for a subscription to either the author or category
        if author_id:
            return Subscription.objects.filter(user=user, author_id=author_id).first()
        elif category_id:
            return Subscription.objects.filter(user=user, category_id=category_id).first()

        return None

    def delete(self, request, *args, **kwargs):
        subscription = self.get_object()
        if subscription:
            subscription.delete()
            return Response({'message': 'Unsubscribed successfully.'}, status=200)
        return Response({'error': 'Subscription not found.'}, status=404)

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


class PostsByCategoryView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'content', 'tags__name']
    ordering_fields = ['published_date']
    
    def get_queryset(self):
        category_id = self.kwargs['category_id']
        queryset = Post.objects.filter(category_id=category_id, status='published')

        # Apply optional filters
        published_date = self.request.query_params.get('published_date')
        tags = self.request.query_params.getlist('tags')
        
        if published_date:
            queryset = queryset.filter(published_date__date=published_date)
        
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()

        return queryset

class PostsByAuthorView(generics.ListAPIView):
    serializer_class = PostSerializer
    pagination_class = StandardResultsSetPagination
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.OrderingFilter, filters.SearchFilter]
    search_fields = ['title', 'content', 'tags__name']
    ordering_fields = ['published_date']
    
    def get_queryset(self):
        author_id = self.kwargs['author_id']
        queryset = Post.objects.filter(author_id=author_id, status='published')

        # Apply optional filters
        published_date = self.request.query_params.get('published_date')
        tags = self.request.query_params.getlist('tags')
        
        if published_date:
            queryset = queryset.filter(published_date__date=published_date)
        
        if tags:
            queryset = queryset.filter(tags__name__in=tags).distinct()

        return queryset





