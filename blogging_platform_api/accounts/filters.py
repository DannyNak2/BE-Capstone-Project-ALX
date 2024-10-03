import django_filters
from .models import Post

class PostFilter(django_filters.FilterSet):
    published_after = django_filters.DateFilter(field_name='published_date', lookup_expr='gte')
    published_before = django_filters.DateFilter(field_name='published_date', lookup_expr='lte')

    class Meta:
        model = Post
        fields = ['category', 'author', 'tags', 'published_after', 'published_before']
