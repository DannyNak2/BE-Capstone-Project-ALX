from django.contrib import admin
from .models import Post, Category, Tag, Comment, User, Subscription
# Register your models here.
admin.site.register(Post)
admin.site.register(Category)
admin.site.register(Tag)
admin.site.register(Comment) 
admin.site.register(User) 
# Consider if admin access for user management is needed
admin.site.register(Subscription)