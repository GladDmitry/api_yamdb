from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models

from reviews.validators import validate_title_year
from users.models import UserProfile
from reviews.constants import (
    MAX_NAME_LENGTH,
    MAX_SCORE,
    MAX_SLUG_LENGTH,
    MIN_SCORE,
    SELF_DESCRIPTION_LENGTH
)


class InfoModel(models.Model):
    """Абстрактная модель."""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Название',
        help_text='Необходимо названия котегории'
    )
    slug = models.SlugField(
        max_length=MAX_SLUG_LENGTH,
        unique=True,
        verbose_name='Индификатор',
        help_text='Необходим индификатор категории',
    )

    class Meta:
        abstract = True

    def __str__(self):
        return self.name


class Category(InfoModel):
    """Модель категории."""

    class Meta:
        ordering = ('name',)
        verbose_name = 'Категория'
        verbose_name_plural = 'Категории'

    def __str__(self):
        return self.name


class Genre(InfoModel):
    """Модель жанра."""

    class Meta:
        ordering = ('name',)
        verbose_name = 'Жанр'
        verbose_name_plural = 'Жанры'

    def __str__(self):
        return self.name


class Title(models.Model):
    """Модель произведения."""

    name = models.CharField(
        max_length=MAX_NAME_LENGTH,
        verbose_name='Название',
        help_text='Необходимо названия произведения',
    )

    description = models.TextField(
        null=True,
        blank=True,
        verbose_name='Описание',
        help_text='Необходимо описание',
    )

    year = models.SmallIntegerField(
        verbose_name='Дата выхода',
        help_text='Укажите дату выхода',
        validators=(validate_title_year,)
    )

    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='titles',
        verbose_name='Категория',
        help_text='Укажите категорию',
    )

    genre = models.ManyToManyField(
        Genre,
        verbose_name='Жанр',
        help_text='Укажите жанр',
    )

    class Meta:
        ordering = ('name',)
        verbose_name = 'Произведение'
        verbose_name_plural = 'Произведения'

    def __str__(self):
        return self.name


class BaseReviewComment(models.Model):
    text = models.TextField(
        verbose_name="Текст",
        help_text="Напишите текст",
    )
    author = models.ForeignKey(
        UserProfile,
        on_delete=models.CASCADE,
        verbose_name="Автор",
    )
    pub_date = models.DateTimeField(
        auto_now_add=True,
        verbose_name="Дата публикации",
    )

    class Meta:
        abstract = True


class Review(BaseReviewComment):
    title = models.ForeignKey(
        Title,
        on_delete=models.CASCADE,
        related_name="reviews",
        verbose_name="Произведение",
    )
    score = models.PositiveSmallIntegerField(
        verbose_name="Рейтинг",
        help_text="Укажите рейтинг от 1 до 10",
        validators=[
            MinValueValidator(MIN_SCORE),
            MaxValueValidator(MAX_SCORE)
        ]
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Отзыв"
        verbose_name_plural = "Отзывы"
        constraints = [
            models.UniqueConstraint(
                fields=["author", "title"], name="unique_review")]

    def __str__(self):
        return self.text[:SELF_DESCRIPTION_LENGTH]


class Comment(BaseReviewComment):
    review = models.ForeignKey(
        Review,
        on_delete=models.CASCADE,
        related_name="comments",
        verbose_name="Отзыв",
    )

    class Meta:
        ordering = ("-pub_date",)
        verbose_name = "Комментарий"
        verbose_name_plural = "Комментарии"

    def __str__(self):
        return self.text[:SELF_DESCRIPTION_LENGTH]
