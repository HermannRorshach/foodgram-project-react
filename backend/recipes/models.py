import re

from django.conf import settings
from django.core.validators import (
    MaxValueValidator,
    MinValueValidator,
    RegexValidator
)
from django.db import models

from users.models import User


class Tag(models.Model):
    name = models.CharField(
        'Название',
        unique=True,
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )
    color = models.CharField(
        'Цвет в hex-код',
        unique=True,
        max_length=settings.HEX_COLOR_LENGTH,
        validators=[RegexValidator(
            regex='^#(?:[A-Fa-f0-9]{3}){1,2}$',
            message='Укажите цвет в формате HEX-код',
            flags=re.IGNORECASE
        )],
        help_text='HEX-код в формате #FFF или #D7ABC9'
    )
    slug = models.SlugField(
        'SLUG',
        unique=True,
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Тег'
        verbose_name_plural = 'Теги'
        ordering = ('name',)

    def __str__(self):
        return self.name[:settings.TRUNCATE_CHARS_LENGTH]


class Ingredient(models.Model):
    name = models.CharField(
        'Название',
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )
    measurement_unit = models.CharField(
        'Единица измерения',
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )

    class Meta:
        verbose_name = 'Ингредиент'
        verbose_name_plural = 'Ингредиенты'
        ordering = ('name',)
        constraints = [models.UniqueConstraint(
            fields=('name', 'measurement_unit'),
            name='unique_ingredient'
        )]

    def __str__(self):
        return (
            f'{self.name[:settings.TRUNCATE_CHARS_LENGTH]} - '
            f'{self.measurement_unit[:settings.TRUNCATE_CHARS_LENGTH]}'
        )


class Recipe(models.Model):
    author = models.ForeignKey(
        User,
        related_name='recipes',
        on_delete=models.CASCADE,
        verbose_name='Автор'
    )
    name = models.CharField(
        'Название',
        max_length=settings.FIELD_DATA_MAX_LENGTH,
        unique=True
    )
    image = models.ImageField('Картинка', upload_to='recipes/images/')
    text = models.TextField('Описание')
    ingredients = models.ManyToManyField(
        Ingredient,
        through='IngredientInRecipe',
        verbose_name='Ингредиенты'
    )
    tags = models.ManyToManyField(
        Tag,
        verbose_name='Теги'
    )
    cooking_time = models.PositiveSmallIntegerField(
        'Время приготовления',
        validators=[
            MinValueValidator(
                settings.MIN_COOKING_TIME,
                message=(f'Минимальное время приготовления '
                         f'{settings.MIN_COOKING_TIME} мин.')
            ),
            MaxValueValidator(
                settings.MAX_COOKING_TIME,
                message=(f'Максимальное время приготовления '
                         f'{settings.MAX_COOKING_TIME} мин.')
            )
        ])

    pub_date = models.DateTimeField(
        'Дата публикации',
        auto_now_add=True
    )

    class Meta:
        verbose_name = 'Рецепт'
        verbose_name_plural = 'Рецепты'
        ordering = ('-pub_date',)

    def __str__(self):
        return self.name[:settings.TRUNCATE_CHARS_LENGTH]


class IngredientInRecipe(models.Model):
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Рецепты'
    )
    ingredient = models.ForeignKey(
        Ingredient,
        on_delete=models.CASCADE,
        related_name='recipe_ingredient',
        verbose_name='Ингредиент'
    )
    amount = models.PositiveSmallIntegerField(
        'Количество',
        validators=[
            MinValueValidator(
                settings.MIN_INGREDIENTS_COUNT,
                message=(f'Минимальное количество ингредиентов '
                         f'{settings.MIN_INGREDIENTS_COUNT}')
            ),
            MaxValueValidator(
                settings.MAX_INGREDIENTS_COUNT,
                message=(f'Максимальное количество ингредиентов '
                         f'{settings.MAX_INGREDIENTS_COUNT}')
            )
        ])

    class Meta:
        verbose_name = 'Ингредиент рецепта'
        verbose_name_plural = 'Ингредиенты рецепта'
        ordering = ('recipe',)
        constraints = [models.UniqueConstraint(
            fields=('recipe', 'ingredient'),
            name='unique_ingredient_in_recipe'
        )]

    def __str__(self):
        return f'{self.recipe.name} - {self.ingredient.name}'


class BaseShoppingCartdFavorite(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        verbose_name='Пользователь',

    )
    recipe = models.ForeignKey(
        Recipe,
        on_delete=models.CASCADE,
        verbose_name='Рецепт',
    )

    class Meta:
        abstract = True
        constraints = [models.UniqueConstraint(
            fields=('user', 'recipe'),
            name='%(app_label)s_%(class)s_unique'
        )]


class ShoppingCart(BaseShoppingCartdFavorite):
    class Meta(BaseShoppingCartdFavorite.Meta):
        default_related_name = 'shopping_carts'
        verbose_name = 'Список покупок'
        verbose_name_plural = 'Список покупок'

    def __str__(self):
        return f'{self.user} добавил {self.recipe.name} в покупки'


class Favorite(BaseShoppingCartdFavorite):
    class Meta(BaseShoppingCartdFavorite.Meta):
        default_related_name = 'favorites'
        verbose_name = 'Избранное'
        verbose_name_plural = 'Избранное'

    def __str__(self):
        return f'{self.user} добавил {self.recipe.name} в избранное'
