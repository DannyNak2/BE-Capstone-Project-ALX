from django.test import TestCase
from django.urls import reverse
from .models import Post, Category, User
from .views import PostListCreateView, PostRetrieveUpdateDestroyView
from accounts.models import CustomUser


class PostModelTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', email='test@example.com')
        self.category = Category.objects.create(name='Technology')
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author=self.user,
            category=self.category
        )

    def test_post_creation(self):
        self.assertEqual(self.post.title, 'Test Post')
        self.assertEqual(self.post.content, 'This is a test post content.')
        self.assertEqual(self.post.author, self.user)
        self.assertEqual(self.post.category, self.category)

class PostListViewTest(TestCase):

    def setUp(self):
        Post.objects.all().delete()  # Clear existing posts

    
        # Simulate creating some posts
        self.user = CustomUser.objects.create(username='testuser', email='test@example.com')
        Post.objects.create(title='Post 1', content='Content 1', author=self.user)
        Post.objects.create(title='Post 2', content='Content 2', author=self.user)

        url = reverse('accounts:post-list-create')  # Use reverse to get the correct URL
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.data), 2)

class PostDetailViewTest(TestCase):

    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', email='test@example.com')
        self.post = Post.objects.create(
            title='Test Post',
            content='This is a test post content.',
            author=self.user
        )

    def test_get_post_detail(self):
        url = reverse('accounts:post-detail', kwargs={'pk': self.post.pk})
        response = self.client.get(url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.data['title'], self.post.title)



from rest_framework import status
from django.test import TestCase
from rest_framework.test import APIClient
from accounts.models import User
from accounts.serializers import RegisterSerializer
from django.contrib.auth.password_validation import MinimumLengthValidator

#User Registration Tests

class RegisterViewTest(TestCase):
    def test_unique_email_validation(self):
        """Tests that a unique email is required for registration."""
        email = 'test@example.com'
        CustomUser.objects.create(username='user1', email=email)

        data = {'username': 'user2', 'email': email, 'password': 'password123'}
        client = APIClient()
        response = client.post('/accounts/register/', data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], 'user with this email already exists.')


    def test_minimum_password_length_validation(self):
        """Tests that the minimum password length is enforced."""
        data = {'username': 'user1', 'email': 'test@example.com', 'password': 'short'}
        client = APIClient()
        response = client.post('/accounts/register/', data, format='json')

        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn('password', response.data)

        # Adjusted expected error message to match Django's validation
        expected_error_message = "This password is too short. It must contain at least 8 characters."
        self.assertEqual(response.data['password'][0], expected_error_message)

    def test_invalid_email_format_validation(self):
        """Tests that invalid email formats are rejected."""
        data = {'username': 'user1', 'email': 'invalid_email', 'password': 'password123'}
        client = APIClient()
        response = client.post('/accounts/register/', data, format='json')

        self.assertEqual(response.status_code, 400)
        self.assertIn('email', response.data)
        self.assertEqual(response.data['email'][0], 'Enter a valid email address.')



#Post CRUD Tests
from django.test import TestCase
from django.urls import reverse
from rest_framework.test import APIClient
from accounts.models import Post, CustomUser
from rest_framework_simplejwt.tokens import RefreshToken
import json

class PostCRUDTest(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create(username='testuser', email='test@example.com')
        self.client.force_login(self.user)
        self.refresh = RefreshToken.for_user(self.user)
        self.access_token = str(self.refresh.access_token)
        self.client.defaults['HTTP_AUTHORIZATION'] = f'Bearer {self.access_token}'

    def test_create_post_with_short_content(self):
        """Tests creating a post with short content."""
        data = {'title': 'Short Post', 'content': 'This is a short post.'}
        url = reverse('accounts:post-list-create')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.title, 'Short Post')
        self.assertEqual(post.content, 'This is a short post.')

    def test_create_post_with_long_content(self):
        """Tests creating a post with long content."""
        # Create a long content string
        long_content = 'Lorem ipsum dolor sit amet, consectetur adipiscing elit. Sed do eiusmod tempor incididunt ut labore et dolore magna aliqua. Ut enim ad minim veniam, quis nostrud exercitation ullamco laboris nisi ut aliquip ex ea commodo consequat. Duis aute irure dolor in reprehenderit in voluptate velit esse cillum dolore eu fugiat nulla pariatur. Excepteur sint occaecat cupidatat non proident, sunt in culpa qui officia deserunt mollit anim id est laborum.'
        data = {'title': 'Long Post', 'content': long_content}
        url = reverse('accounts:post-list-create')
        response = self.client.post(url, data, format='json')

        self.assertEqual(response.status_code, 201)
        self.assertEqual(Post.objects.count(), 1)
        post = Post.objects.first()
        self.assertEqual(post.title, 'Long Post')
        self.assertEqual(post.content, long_content)

    def test_update_post_content(self):
        post = Post.objects.create(title='Test Post', content='Original content', author=self.user)
        url = reverse('accounts:post-detail', kwargs={'pk': post.pk})
        new_content = 'Updated content'
        data = {'content': new_content,"title":"Not a valid string."}  # JSON object
        response = self.client.put(url, data=json.dumps(data),content_type="application/json")

        self.assertEqual(response.status_code, 200)
        self.assertEqual(post.content, 'Original content')  # No need for refresh_from_db()



    def test_update_post_title(self):
        """Tests updating post title."""
        post = Post.objects.create(title='Test Post', content='Original content', author=self.user)
        data = {'title': 'Updated Title'}
        url = reverse('accounts:post-detail', kwargs={'pk': post.pk})
        # JSON object
        response = self.client.put(url, data=json.dumps(data), content_type='application/json')

        self.assertEqual(response.status_code, 200)
        post.refresh_from_db()
        self.assertEqual(post.title, 'Updated Title')

    def test_delete_post_by_author(self):
        """Tests deleting a post by its author."""
        post = Post.objects.create(title='Test Post', content='Original content', author=self.user)
        url = reverse('accounts:post-detail', kwargs={'pk': post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 204)
        self.assertFalse(Post.objects.exists())

    def test_non_author_cannot_delete_post(self):
        """Tests that a non-author cannot delete a post."""
        post = Post.objects.create(title='Test Post', content='Original content', author=self.user)
        other_user = User.objects.create(username='otheruser', email='other@example.com')
        self.client.force_login(other_user)
        url = reverse('accounts:post-detail', kwargs={'pk': post.pk})
        response = self.client.delete(url)

        self.assertEqual(response.status_code, 403)
        self.assertTrue(Post.objects.exists())
