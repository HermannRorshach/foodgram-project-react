from rest_framework.mixins import (ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.viewsets import GenericViewSet


class CreateListRetrieveMixin(ListModelMixin,
                              RetrieveModelMixin,
                              GenericViewSet):
    """Набор представлений, предоставляющий действия
    «получить», «создать» и «список»."""
    pass
