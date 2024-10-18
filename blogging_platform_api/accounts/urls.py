from django.urls import path
from .views import (
    RegisterView, ProfileView, PostListCreateView, PostRetrieveUpdateDestroyView, share_post_via_email,
    DraftPostListView, CommentListCreateView, TopLikedPostsView, TopRatedPostsView, SubscriptionView, 
    UnsubscribeView, NewPostNotification, LikePostView, RatePostView, CommentUpdateDestroyView, 
    SharePostView, PostsByCategoryView, PostsByAuthorView, UnsubscribeView,CustomLoginView
)
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

app_name = 'accounts'

urlpatterns = [
    #User Registration and Authentication
    path('register/', RegisterView.as_view(), name='register'),
    path('', CustomLoginView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),
    #path('profile/<str:username>/', ProfileView.as_view(), name='profile'),


    #Post Management
    path('posts/', PostListCreateView.as_view(), name='post-list-create'),
    path('posts/drafts/', DraftPostListView.as_view(), name='draft-posts'),
    path('posts/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post-retrieve-update-destroy'),
    
    #Comments Management
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('posts/<int:post_id>/comments/<int:comment_pk>/', CommentUpdateDestroyView.as_view(), name='comment-update-destroy'),
    
    #Post Features
    path('posts/top-liked/', TopLikedPostsView.as_view(), name='top-liked-posts'),
    path('posts/top-rated/', TopRatedPostsView.as_view(), name='top-rated-posts'),
    
    #Subscription Management
    path('subscribe/', SubscriptionView.as_view(), name='subscribe'),
    path('unsubscribe/<int:pk>/', UnsubscribeView.as_view(), name='unsubscribe'),
    path('new-post/', NewPostNotification.as_view(), name='new-post-notification'),
    
    #Post Interaction
    path('posts/<int:pk>/like/', LikePostView.as_view(), name='like-post'),
    path('posts/<int:pk>/rate/', RatePostView.as_view(), name='rate-post'),
    path('posts/<int:pk>/share/', SharePostView.as_view(), name='share-post'),
    
    #Post search and filter by category and author
    path('posts/category/<int:category_id>/', PostsByCategoryView.as_view(), name='posts-by-category'),
    path('posts/author/<int:author_id>/', PostsByAuthorView.as_view(), name='posts-by-author'),
]
