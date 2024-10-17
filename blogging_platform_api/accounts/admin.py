from django.contrib import admin
from .models import Post, Category, Tag, Comment, Subscription, CustomUser

class PostAdmin(admin.ModelAdmin):
    list_display = ('author', 'title', 'category', 'status', 'published_date')
    search_fields = ('title', 'content', 'author__username')
    list_filter = ('status', 'category', 'tags')
    date_hierarchy = 'published_date'
    prepopulated_fields = {'title': ('content',)}  # Automatically fill title based on content
    
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class TagAdmin(admin.ModelAdmin):
    list_display = ('id', 'name')
    search_fields = ('name',)

class CommentAdmin(admin.ModelAdmin):
    list_display = ('user', 'post', 'created_at', 'parent_comment')
    search_fields = ('user__username', 'post__title', 'content')
    list_filter = ('created_at', 'post')

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id', 'user', 'author', 'category')
    list_filter = ('author', 'category')

class UserAdmin(admin.ModelAdmin):
    list_display = ('id', 'username', 'email')
    search_fields = ('username', 'email')

# Register models in the admin site
admin.site.register(Post, PostAdmin)
admin.site.register(Category, CategoryAdmin)
admin.site.register(Tag, TagAdmin)
admin.site.register(Comment, CommentAdmin)
admin.site.register(CustomUser, UserAdmin)
admin.site.register(Subscription, SubscriptionAdmin)
