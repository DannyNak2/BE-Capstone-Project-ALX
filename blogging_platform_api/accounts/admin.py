from django.contrib import admin
from .models import Post, Category, Tag, Comment, User, Subscription
# Register your models here.



class PostAdmin(admin.ModelAdmin):
    list_display = ('author','title', 'content', 'category','status')

class CategoryAdmin(admin.ModelAdmin):
    list_display = ('id','name' )

class SubscriptionAdmin(admin.ModelAdmin):
    list_display = ('id','author' )

class UserAdmin(admin.ModelAdmin):
    list_display = ('id','username', 'email' )

admin.site.register(Post,PostAdmin)
admin.site.register(Category,CategoryAdmin)
admin.site.register(Tag)
admin.site.register(Comment) 
admin.site.register(User,UserAdmin) 
# Consider if admin access for user management is needed
admin.site.register(Subscription,SubscriptionAdmin)

