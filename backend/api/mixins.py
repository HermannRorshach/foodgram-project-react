from rest_framework.mixins import (ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.viewsets import GenericViewSet


class ListRetrieveMixin(ListModelMixin,
                        RetrieveModelMixin,
                        GenericViewSet):
    """Набор представлений, предоставляющий действия
    «получить», «создать» и «список»."""
    pass
