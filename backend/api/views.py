from django.db.models import Sum
from django_filters.rest_framework import DjangoFilterBackend
from django.http import FileResponse
from django.shortcuts import get_object_or_404
from djoser.views import UserViewSet

from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.permissions import (IsAuthenticated,
                                        IsAuthenticatedOrReadOnly)
from rest_framework.response import Response
from rest_framework.status import (
    HTTP_201_CREATED,
    HTTP_204_NO_CONTENT
)
from rest_framework.viewsets import ModelViewSet

from api.filters import IngredientFilter, RecipeFilter
from api.mixins import ListRetrieveMixin
from api.pagination import CustomPaginator
from api.serializers import (
    CreateRecipeSerializer,
    CustomUserSerializer,
    FavoriteSerializer,
    IngredientSerializer,
    ShoppingCartSerializer,
    SubscriptionCreateSerializer,
    SubscriptionSerializer,
    RecipeListSerializer,
    TagSerializer
)
from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


class TagViewSet(ListRetrieveMixin):
    serializer_class = TagSerializer
    queryset = Tag.objects.all()
    permission_classes = (IsAuthenticatedOrReadOnly,)
    pagination_class = None


class IngredientViewSet(ListRetrieveMixin):
    queryset = Ingredient.objects.all()
    serializer_class = IngredientSerializer
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend, SearchFilter)
    filterset_class = IngredientFilter
    pagination_class = None


class CustomUserViewSet(UserViewSet):
    queryset = User.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = (IsAuthenticated,)
    pagination_class = CustomPaginator
    lookup_field = 'id'

    @action(detail=True, methods=['POST', 'DELETE'])
    def subscribe(self, request, id=None):
        user = request.user
        author = get_object_or_404(User, id=id)

        if request.method == 'POST':
            serializer = SubscriptionCreateSerializer(
                data={'user': user.id, 'author': author.id},
                context={'request': request}
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data, status=HTTP_201_CREATED)

        get_object_or_404(
            Subscription,
            user=request.user,
            author=get_object_or_404(User, id=id)
        ).delete()
        return Response(status=HTTP_204_NO_CONTENT)

    @action(detail=False, methods=['GET'])
    def subscriptions(self, request):
        queryset = User.objects.filter(following__user=request.user)
        page = self.paginate_queryset(queryset)
        serializer = SubscriptionSerializer(
            page,
            many=True,
            context={'request': request}
        )
        return self.get_paginated_response(serializer.data)


class RecipeViewSet(ModelViewSet):
    queryset = (
        Recipe.objects.select_related('author')
        .prefetch_related('ingredients', 'tags').all()
    )
    permission_classes = (IsAuthenticatedOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = RecipeFilter
    pagination_class = CustomPaginator
    http_method_names = ['get', 'post', 'patch', 'delete']

    def perform_update(self, serializer):
        return serializer.save(author=self.request.user)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.validated_data['author'] = self.request.user
        serializer.save()
        serializer = CreateRecipeSerializer(
            instance=serializer.instance,
            context={'request': self.request}
        )

        return Response(
            serializer.data,
            status=HTTP_201_CREATED,
            headers=self.get_success_headers(serializer.data)
        )

    def get_serializer_class(self):
        if self.request.method == 'GET':
            return RecipeListSerializer
        return CreateRecipeSerializer

    @action(detail=True, methods=['POST'])
    def shopping_cart(self, request, pk):
        return self._add_recipe(request, pk, ShoppingCartSerializer)

    @shopping_cart.mapping.delete
    def destroy_shopping_cart(self, request, pk):
        return self._del_recipe(request, pk, ShoppingCart)

    @action(detail=True, methods=['POST'])
    def favorite(self, request, pk):
        return self._add_recipe(request, pk, FavoriteSerializer)

    @favorite.mapping.delete
    def destroy_favorite(self, request, pk):
        return self._del_recipe(request, pk, Favorite)

    @action(detail=False, methods=['GET'])
    def download_shopping_cart(self, request):
        filename = 'shop_list.txt'
        context, headers = self._make_file(request, filename)

        with open(filename, 'w', encoding='UTF-8') as file:
            file.write(context)

        return FileResponse(open(filename, 'rb'), headers=headers)

    @staticmethod
    def _make_file(request, file_name):
        ingredients = IngredientInRecipe.objects.filter(
            recipe__shopping_carts__user=request.user
        ).values(
            'ingredient__name',
            'ingredient__measurement_unit'
        ).annotate(total_amount=Sum('amount')).order_by('ingredient__name')

        shop_list = ''
        curr_ingredient = None
        total_amount = 0

        for ingredient in ingredients:
            name = ingredient.get('ingredient__name')
            measurement_unit = ingredient.get('ingredient__measurement_unit')
            ingredient_amount = ingredient.get('total_amount')

            if curr_ingredient and curr_ingredient != name:
                shop_list += (f'{curr_ingredient} {measurement_unit} - '
                              f'{total_amount}\n')
                total_amount = 0

            curr_ingredient = name
            total_amount += ingredient_amount

        if curr_ingredient:
            shop_list += (f'{curr_ingredient} {measurement_unit} - '
                          f'{total_amount}\n')

        headers = {
            'Content-Disposition': f'attachment; filename={file_name}'
        }

        return shop_list, headers

    @staticmethod
    def _add_recipe(request, pk, serializer_class):
        recipe = get_object_or_404(Recipe, id=pk)
        data = {'recipe': recipe.id, 'user': request.user.id}
        serializer = serializer_class(data=data, context={'request': request})
        serializer.is_valid(raise_exception=True)
        serializer.save()

        return Response(serializer.data, status=HTTP_201_CREATED)

    @staticmethod
    def _del_recipe(request, pk, serializer_class):
        get_object_or_404(
            serializer_class,
            recipe__id=pk,
            user=request.user
        ).delete()
        return Response(status=HTTP_204_NO_CONTENT)
