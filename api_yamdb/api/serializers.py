from django.conf import settings
from django.core.validators import EmailValidator
from django.utils.translation import gettext as _
from rest_framework import serializers
from django.shortcuts import get_object_or_404
from django.db import IntegrityError

from reviews.models import Category, Comment, Genre, Review, Title
from reviews.validators import validate_title_year
from users.models import UserProfile, User, validate_username


class SignUpSerializer(serializers.Serializer):
    """
    Сериализатор для регистрации нового пользователя
    или повторного запроса кода подтверждения.
    Проверяет корректность введенных данных и создает пользователя.
    """

    email = serializers.EmailField(
        required=True, max_length=254, validators=[EmailValidator()]
    )
    username = serializers.RegexField(
        r"^[\w.@+-]{1,150}$", required=True, validators=[validate_username]
    )

    def create(self, validated_data):
        """
        Создает нового пользователя или возвращает существующего.
        Отправляет код подтверждения на email.
        """
        try:
            user, created = UserProfile.objects.get_or_create(
                email=validated_data["email"],
                username=validated_data["username"]
            )
            return user
        except IntegrityError as e:
            raise serializers.ValidationError({"detail": str(e)})


class AuthTokenSerializer(serializers.Serializer):
    """
    Сериализатор для аутентификации пользователя с использованием
    имени пользователя и кода подтверждения.
    """

    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=50)

    def validate(self, data):
        """
        Проверяет корректность введенных данных для аутентификации.
        Убеждается, что пользователь существует и код подтверждения правильный.
        """
        username = data["username"]
        confirmation_code = data["confirmation_code"]
        user = get_object_or_404(UserProfile, username=username)

        if not user.verify_confirmation_code(confirmation_code):
            raise serializers.ValidationError("Неправильный код подтверждения")

        data["user"] = user
        return data


class GenreSerializer(serializers.ModelSerializer):
    class Meta:
        model = Genre
        fields = ('name', 'slug')
        lookup_field = 'slug'


class CategorySerializer(serializers.ModelSerializer):
    class Meta:
        model = Category
        fields = ('name', 'slug')
        lookup_field = 'slug'


class TitleReadSerializer(serializers.ModelSerializer):
    category = CategorySerializer(read_only=True)
    genre = GenreSerializer(
        read_only=True,
        many=True
    )
    rating = serializers.IntegerField(read_only=True)

    class Meta:
        fields = '__all__'
        model = Title


class TitleWriteSerializer(serializers.ModelSerializer):
    category = serializers.SlugRelatedField(
        queryset=Category.objects.all(),
        slug_field='slug'
    )
    genre = serializers.SlugRelatedField(
        queryset=Genre.objects.all(),
        slug_field='slug',
        many=True
    )

    class Meta:
        fields = '__all__'
        model = Title

    def validate_year(self, value):
        return validate_title_year(value)


class ReviewSerializer(serializers.ModelSerializer):
    title = serializers.SlugRelatedField(
        read_only=True,
        slug_field="name"
    )
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )

    def validate(self, data):
        request = self.context.get('request')
        title_id = self.context['view'].kwargs.get('title_id')
        if request.method == 'POST':
            if Review.objects.filter(
                author=request.user,
                title_id=title_id
            ).exists():
                raise serializers.ValidationError(
                    'Вы уже оставили отзыв на это произведение'
                )
        return data

    class Meta:
        model = Review
        fields = ("id", "title", "text", "author", "score", "pub_date")


class CommentSerializer(serializers.ModelSerializer):
    author = serializers.SlugRelatedField(
        read_only=True,
        slug_field="username"
    )

    class Meta:
        model = Comment
        fields = ("id", "text", "author", "pub_date")


class UserSerializer(serializers.ModelSerializer):
    """
    Сериализатор для представления и валидации данных пользователя.
    """

    email = serializers.EmailField(
        max_length=254,
        validators=[EmailValidator()]
    )
    username = serializers.RegexField(
        r"^[\w.@+-]{1,150}$", required=True, validators=[validate_username]
    )

    class Meta:
        model = User
        fields = (
            "username", "email", "first_name",
            "last_name", "bio", "role"
        )
        extra_kwargs = {
            "username": {"required": True, "allow_blank": False},
            "email": {"required": True, "allow_blank": False},
        }

    def create(self, validated_data):
        try:
            return super().create(validated_data)
        except IntegrityError as e:
            raise serializers.ValidationError({"detail": str(e)})
