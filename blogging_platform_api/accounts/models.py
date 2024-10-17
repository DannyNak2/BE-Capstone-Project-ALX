from django.contrib.auth.models import AbstractUser, User
from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.db.models import Avg, Count
from django.urls import reverse

class CustomUser(AbstractUser):
    email = models.EmailField(unique=True)
    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    def __str__(self):
        return self.email

User = get_user_model()

class Category(models.Model):
    name = models.CharField(max_length=100)
    description = models.TextField(blank=True, null=True)
    
    def __str__(self):
        return self.name

class Post(models.Model):
    title = models.CharField(max_length=255)
    content = models.TextField()
    author = models.ForeignKey(User,  related_name='authored_posts', on_delete=models.CASCADE)
    category = models.ForeignKey(Category, on_delete=models.SET_NULL, null=True)
    tags = models.ManyToManyField('Tag', blank=True)
    published_date = models.DateTimeField(default=timezone.now)
    created_at = models.DateTimeField(auto_now_add=True)
    likes = models.ManyToManyField(User, related_name='liked_posts', blank=True)
    ratings = models.ManyToManyField(User, related_name='rated_posts', through='PostRating')
    status = models.CharField(max_length=10, choices=[('draft', 'Draft'), ('published', 'Published')], default='draft')

    def __str__(self):
        return self.title
    
    def get_absolute_url(self):
        return reverse('accounts:post-retrieve-update-destroy', args=[str(self.id)])
    
    def average_rating(self):
        ratings = PostRating.objects.filter(post=self)
        if ratings.exists():
            return sum(rating.rating for rating in ratings) / ratings.count()
        return 0

    def likes_count(self):
        return PostLike.objects.filter(post=self).count()

class Tag(models.Model):
    name = models.CharField(max_length=50)

    def __str__(self):
        return self.name
    
class Comment(models.Model):
    user = models.ForeignKey(User, related_name='comments', on_delete=models.CASCADE)
    post = models.ForeignKey(Post, related_name='comments', on_delete=models.CASCADE)
    content = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    parent_comment = models.ForeignKey('self', null=True, blank=True, related_name='replies', on_delete=models.CASCADE)

    def __str__(self):
        return f"Comment by {self.user.username} on {self.post.title}"


class PostRating(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    rating = models.PositiveIntegerField(choices=[(1, '1 Star'), (2, '2 Stars'), (3, '3 Stars'), (4, '4 Stars'), (5, '5 Stars')])

    class Meta:
        unique_together = ('post', 'user')  # Ensure users can't rate the same post multiple times

class PostLike(models.Model):
    post = models.ForeignKey(Post, on_delete=models.CASCADE)
    user = models.ForeignKey(User, on_delete=models.CASCADE)

    class Meta:
        unique_together = ('post', 'user')  # Ensure users can't like the same post multiple times

class Profile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='profile')
    bio = models.TextField(blank=True) 

    profile_picture = models.ImageField(upload_to='profile_pics/', blank=True)

    def __str__(self):
        return f"{self.user.username}'s Profile"
    
    def get_absolute_url(self):
        return reverse('profile-detail', kwargs={'username': self.user.username})

@receiver(post_save, sender=User)
def create_profile(sender, instance, created, **kwargs):
    if created:
        Profile.objects.create(user=instance) 


@receiver(post_save, sender=User)
def save_profile(sender, instance, **kwargs):
    instance.profile.save() 


class Subscription(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE)
    # Choose either author or category
    author = models.ForeignKey(User, on_delete=models.CASCADE, related_name='subscribers', blank=True, null=True)
    category = models.ForeignKey('accounts.Category', on_delete=models.CASCADE, related_name='subscribers', blank=True, null=True)

    class Meta:
        unique_together = (('user', 'author'), ('user', 'category'))  # Prevent duplicate subscriptions

    def __str__(self):
        if self.author:
            return f"{self.user.username} subscribed to {self.author.username}"
        else:
            return f"{self.user.username} subscribed to category {self.category.name}"