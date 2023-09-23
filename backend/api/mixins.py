from rest_framework.mixins import (ListModelMixin,
                                   RetrieveModelMixin)
from rest_framework.viewsets import GenericViewSet


class CustomViewMixin(ListModelMixin,
                      RetrieveModelMixin,
                      GenericViewSet):
    pass
