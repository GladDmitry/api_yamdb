from rest_framework.pagination import PageNumberPagination
from django.conf import settings


class CustomPageNumberPagination(PageNumberPagination):
    """
    Пользовательская пагинация для API.
    Размер страницы устанавливается из настроек.
    """
    page_size = settings.CUSTOM_PAGE_SIZE