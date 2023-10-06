from django.conf import settings
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.validators import UnicodeUsernameValidator
from django.core.exceptions import ValidationError
from django.db import models


class User(AbstractUser):
    email = models.EmailField(
        'E-mail',
        max_length=settings.FIELD_DATA_MAX_LENGTH,
        unique=True
    )
    username = models.CharField(
        'Имя пользователя',
        max_length=settings.FIELD_DATA_MAX_LENGTH,
        unique=True,
        validators=(UnicodeUsernameValidator(),)
    )
    first_name = models.CharField(
        'Имя',
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )
    last_name = models.CharField(
        'Фамилия',
        max_length=settings.FIELD_DATA_MAX_LENGTH
    )

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ('username', 'first_name', 'last_name')

    class Meta:
        verbose_name = 'Пользователь'
        verbose_name_plural = 'Пользователи'
        ordering = ('username',)

    def __str__(self):
        return str(self.username)


class Subscription(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='follower',
        verbose_name='Подписчик'
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='following',
        verbose_name='Автор'
    )

    class Meta:
        verbose_name = 'Подписка'
        verbose_name_plural = 'Подписки'
        constraints = [models.UniqueConstraint(
            fields=['user', 'author'],
            name='unique_subscriptions'
        )]

    def clean(self):
        if self.user == self.author:
            raise ValidationError("Подписка на себя запрещено!")

    def __str__(self):
        return f'{self.user} подписался на {self.author}'
