from django.conf import settings
from django.db import transaction
from djoser.serializers import UserCreateSerializer
from drf_extra_fields.fields import Base64ImageField
from rest_framework.serializers import (
    IntegerField,
    ModelSerializer,
    PrimaryKeyRelatedField,
    ReadOnlyField,
    SerializerMethodField,
    ValidationError
)
from rest_framework.validators import UniqueTogetherValidator

from recipes.models import (
    Favorite,
    Ingredient,
    IngredientInRecipe,
    Recipe,
    ShoppingCart,
    Tag
)
from users.models import Subscription, User


class CustomUserCreateSerializer(UserCreateSerializer):
    """Создание пользователя."""

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'password'
        )


class CustomUserSerializer(ModelSerializer):
    """Получает информацию о том, подписан ли текущий пользователь
    на пользователя из контекста запроса.
    """

    is_subscribed = SerializerMethodField(read_only=True)

    class Meta:
        model = User
        fields = (
            'id',
            'email',
            'username',
            'first_name',
            'last_name',
            'is_subscribed'
        )

    def get_is_subscribed(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and user.follower.all().filter(author=obj.id).exists())


class TagSerializer(ModelSerializer):
    class Meta:
        model = Tag
        fields = ('id', 'name', 'color', 'slug')


class IngredientSerializer(ModelSerializer):
    class Meta:
        model = Ingredient
        fields = ('id', 'name', 'measurement_unit')


class IngredientInRecipeSerializer(ModelSerializer):
    id = ReadOnlyField(source='ingredient.id')
    name = ReadOnlyField(source='ingredient.name')
    measurement_unit = ReadOnlyField(source='ingredient.measurement_unit')

    class Meta:
        model = IngredientInRecipe
        fields = (
            'id',
            'name',
            'measurement_unit',
            'amount'
        )


class AddIngredientSerializer(ModelSerializer):
    id = PrimaryKeyRelatedField(queryset=Ingredient.objects.all())

    def validate_amount(self, value):
        if value <= 0:
            raise ValidationError('Количество не должно быть нулевым')
        return value

    class Meta:
        model = IngredientInRecipe
        fields = ('id', 'amount')


class RecipeMinifiedSerializer(ModelSerializer):
    """Базовая информация о рецепте."""

    image = Base64ImageField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'image',
            'cooking_time'
        )


class SubscriptionSerializer(CustomUserSerializer):
    """Информация о подписке пользователя на автора рецептов."""

    id = ReadOnlyField(source='author.id')
    username = ReadOnlyField(source='author.username')
    first_name = ReadOnlyField(source='author.first_name')
    last_name = ReadOnlyField(source='author.last_name')
    recipes = SerializerMethodField()
    recipes_count = SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'username',
            'first_name',
            'last_name',
            'is_subscribed',
            'recipes',
            'recipes_count'
        )

    def get_recipes(self, obj):
        request = self.context.get('request')
        recipes_limit = request.query_params.get('recipes_limit')

        queryset = None
        if recipes_limit:
            queryset = obj.author.recipes.all()[:int(recipes_limit)]
        else:
            queryset = obj.author.recipes.all()

        return RecipeMinifiedSerializer(queryset, many=True).data

    def get_recipes_count(self, obj):
        return obj.author.recipes.all().count()


class RecipeListSerializer(ModelSerializer):
    """Получение полной информации о рецепте."""

    author = CustomUserSerializer(read_only=True)
    tags = TagSerializer(read_only=True, many=True)
    image = Base64ImageField()
    is_favorited = SerializerMethodField()
    is_in_shopping_cart = SerializerMethodField()
    ingredients = IngredientInRecipeSerializer(
        many=True,
        source='recipe_ingredient'
    )

    class Meta:
        model = Recipe
        fields = (
            'id',
            'author',
            'tags',
            'ingredients',
            'name',
            'image',
            'text',
            'cooking_time',
            'is_favorited',
            'is_in_shopping_cart',
        )

    def get_ingredients(self, obj):
        ingredients_list = IngredientInRecipe.objects.filter(recipe=obj)
        return IngredientInRecipeSerializer(ingredients_list, many=True).data

    def get_is_favorited(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and obj.favorites.filter(user=user).exists())

    def get_is_in_shopping_cart(self, obj):
        user = self.context.get('request').user
        return (user.is_authenticated
                and obj.shopping_carts.filter(user=user).exists())


class CreateRecipeSerializer(ModelSerializer):
    """Создание и обновление рецепта."""

    tags = PrimaryKeyRelatedField(
        many=True,
        queryset=Tag.objects.all()
    )
    ingredients = AddIngredientSerializer(many=True)
    image = Base64ImageField()
    cooking_time = IntegerField()

    class Meta:
        model = Recipe
        fields = (
            'id',
            'name',
            'tags',
            'ingredients',
            'text',
            'image',
            'cooking_time'
        )

    def create_tags(self, tags, recipe):
        recipe.tags.add(*tags)

    def create_ingredients(self, ingredients, recipe):
        for ingredient in ingredients:
            IngredientInRecipe.objects.get_or_create(
                recipe=recipe,
                ingredient=ingredient['id'],
                amount=ingredient['amount']
            )

    def validate_cooking_time(self, value):
        if value and int(value) > settings.MAX_INGREDIENTS_COUNT:
            raise ValidationError(
                f'Максимальное время приготовления '
                f'{settings.MAX_COOKING_TIME} мин.'
            )
        return value

    @transaction.atomic
    def create(self, validated_data):
        ingredients_list = validated_data.pop('ingredients')
        tags_list = validated_data.pop('tags')

        recipe = Recipe.objects.create(**validated_data)
        self.create_ingredients(ingredients_list, recipe)
        self.create_tags(tags_list, recipe)

        return recipe

    @transaction.atomic
    def update(self, instance, validated_data):
        instance.tags.clear()
        instance.ingredients.clear()
        tags_list = validated_data.pop('tags')
        ingredients_list = validated_data.pop('ingredients')

        instance.tags.set(tags_list)
        self.create_ingredients(ingredients_list, instance)
        self.create_tags(tags_list, instance)

        return super().update(instance, validated_data)

    def to_representation(self, instance):
        return RecipeListSerializer(
            instance,
            context={'request': self.context.get('request')}
        ).data


class BaseShoppingCartFavoriteSerializer(ModelSerializer):
    """Базовый для ShoppingCartSerializer и  FavoriteSerializer."""

    def to_representation(self, instance):
        return RecipeMinifiedSerializer(
            instance.recipe,
            context={'request': self.context.get('request')}
        ).data


class ShoppingCartSerializer(BaseShoppingCartFavoriteSerializer):
    class Meta:
        model = ShoppingCart
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=ShoppingCart.objects.all(),
                fields=('user', 'recipe'),
                message='Вы уже добавили рецепт в список покупок!'
            )
        ]


class FavoriteSerializer(BaseShoppingCartFavoriteSerializer):
    class Meta:
        model = Favorite
        fields = ('user', 'recipe')
        validators = [
            UniqueTogetherValidator(
                queryset=Favorite.objects.all(),
                fields=['user', 'recipe'],
                message='Вы уже добавили рецепт в избранное'
            )
        ]
