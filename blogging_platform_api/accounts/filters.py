import django_filters
from .models import Post

class PostFilter(django_filters.FilterSet):
    published_date = django_filters.DateFromToRangeFilter(field_name='published_date')
    category = django_filters.CharFilter(field_name='category__name', lookup_expr='icontains')
    tags = django_filters.CharFilter(field_name='tags__name', lookup_expr='icontains')

    class Meta:
        model = Post
        fields = ['category', 'published_date', 'tags']



