from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.exceptions import ValidationError
from django.conf import settings
from django.contrib.auth.tokens import default_token_generator
from django.contrib.auth.validators import UnicodeUsernameValidator

from .constants import (
    MAX_USERNAME_LENGTH,
    MAX_EMAIL_LENGTH,
    USER_ROLE,
    MODERATOR_ROLE,
    ADMIN_ROLE,
    ROLE_CHOICES,
    MAX_ROLE_LENGTH,
)


def validate_username(value):
    if value.lower() == settings.NOT_ALLOWED_USERNAME:
        raise ValidationError(
            "Использование имени пользователя 'me' запрещено."
        )


class UserProfile(AbstractUser):
    """Модель пользователя"""

    username = models.CharField(
        max_length=MAX_USERNAME_LENGTH,
        unique=True,
        verbose_name="Имя пользователя",
        help_text="Введите имя пользователя (максимум 150 символов).",
        validators=[UnicodeUsernameValidator(), validate_username],
    )

    role = models.CharField(
        max_length=MAX_ROLE_LENGTH,
        choices=ROLE_CHOICES,
        default=USER_ROLE,
        verbose_name="Уровень доступа пользователя",
        help_text="Уровень доступа пользователя",
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Биография пользователя",
        help_text="Напишите информацию о себе",
    )

    email = models.EmailField(
        unique=True,
        verbose_name="Электронная почту пользователя",
        help_text="Введите свою почту",
        max_length=MAX_EMAIL_LENGTH,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("username",)

    def __str__(self):
        return self.username

    @property
    def is_moderator(self):
        return self.role == MODERATOR_ROLE

    @property
    def is_admin(self):
        return self.role == ADMIN_ROLE or self.is_superuser or self.is_staff

    @property
    def confirmation_code(self):
        return default_token_generator.make_token(self)

    def verify_confirmation_code(self, token):
        return default_token_generator.check_token(self, token)


User = get_user_model()
