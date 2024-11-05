from django_filters.rest_framework import CharFilter, FilterSet, NumberFilter

from reviews.models import Title


class FilterTitle(FilterSet):
    genre = CharFilter(field_name='genre__slug', lookup_expr='icontains')
    category = CharFilter(field_name='category__slug', lookup_expr='icontains')

    class Meta:
        model = Title
        fields = ('category', 'genre', 'name', 'year')
