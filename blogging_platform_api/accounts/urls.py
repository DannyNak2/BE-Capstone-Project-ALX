from django.urls import path
from .views import RegisterView, ProfileView, PostListCreateView, PostRetrieveUpdateDestroyView, share_post_via_email
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView
from .views import CommentListCreateView, TopLikedPostsView, TopRatedPostsView, SubscriptionView, UnsubscribeView, NewPostNotification,LikePostView,RatePostView,CommentUpdateDestroyView,SharePostView,PostDeleteView, PostsByCategoryView, PostsByAuthorView

app_name = 'accounts'

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', TokenObtainPairView.as_view(), name='login'),
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    path('profile/', ProfileView.as_view(), name='profile'),

    path('posts/', PostListCreateView.as_view(), name='post-list-create'),

    path('posts/<int:pk>/', PostRetrieveUpdateDestroyView.as_view(), name='post-retrieve-update-destroy'),
    
    path('posts/<int:post_id>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('posts/<int:pk>/like/', TopLikedPostsView.as_view(), name='like-post'),
    path('posts/top-rated/', TopRatedPostsView.as_view(), name='top-rated-posts'),
    
    path('posts/drafts/', PostListCreateView.as_view(), name='draft-post-list'),
    path('profile/', ProfileView.as_view(), name='profile'),
    path('subscribe/', SubscriptionView.as_view(), name='subscribe'),
    path('unsubscribe/<int:pk>/', UnsubscribeView.as_view(), name='unsubscribe'),
    path('new-post/', NewPostNotification.as_view(), name='new-post-notification'),
    path('posts/<int:pk>/like/', LikePostView.as_view(), name='like-post'),
    path('posts/<int:pk>/rate/', RatePostView.as_view(), name='rate-post'),
    path('posts/<int:pk>/comments/', CommentListCreateView.as_view(), name='comment-list-create'),
    path('posts/<int:pk>/comments/<int:comment_pk>/', CommentUpdateDestroyView.as_view(), name='comment-detail'),
    path('posts/<int:pk>/share/', SharePostView.as_view(), name='share-post'),
    path('posts/<int:pk>/', PostDeleteView.as_view(), name='post-delete'),
    path('posts/category/<int:category_id>/', PostsByCategoryView.as_view(), name='posts-by-category'),
    path('posts/author/<int:author_id>/', PostsByAuthorView.as_view(), name='posts-by-author'),

]
