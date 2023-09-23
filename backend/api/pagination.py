from django.conf import settings
from rest_framework.pagination import PageNumberPagination


class CustomPaginator(PageNumberPagination):
    page_size_query_param = 'limit'
    page_size = settings.COUNT_RECIPES_ON_HOME_PAGE
