from django.contrib.auth import get_user_model
from django.contrib.auth.models import AbstractUser
from django.db import models


class CustomUser(AbstractUser):
    """Модель пользователя"""

    USER = "user"
    MODERATOR = "moderator"
    ADMIN = "admin"

    CHOICES = (
        (USER, "Аутентифицированный пользователь"),
        (MODERATOR, "Модератор"),
        (ADMIN, "Админ"),
    )

    username = models.CharField(
        max_length=150,
        unique=True,
        verbose_name="Имя пользователя",
        help_text="Введите имя пользователя (максимум 150 символов)."
    )

    role = models.CharField(
        max_length=13,
        choices=CHOICES,
        default="user",
        verbose_name="Уровень доступа пользователя",
        help_text="Уровень доступа пользователя",
    )

    bio = models.TextField(
        blank=True,
        verbose_name="Биография пользователя",
        help_text="Напишите информацию о себе",
    )

    email = models.EmailField(
        blank=False,
        unique=True,
        verbose_name="Электронная почту пользователя",
        help_text="Введите свою почту",
        max_length=254,
    )

    confirmation_code = models.CharField(
        blank=True,
        verbose_name="Код подтверждения",
        max_length=50,
    )

    class Meta:
        verbose_name = "Пользователь"
        verbose_name_plural = "Пользователи"
        ordering = ("-id",)

    def __str__(self):
        return self.username

    @property
    def is_user(self):
        return self.role == self.USER

    @property
    def is_moderator(self):
        return self.role == self.MODERATOR

    @property
    def is_admin(self):
        return self.role == self.ADMIN


User = get_user_model()