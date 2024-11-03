from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from rest_framework.exceptions import NotFound
from django.utils.translation import gettext as _

from users.models import CustomUser
from reviews.models import Category, Comment, Genre, Review, Title
from reviews.validators import validate_title_year
from users.models import User


class SignUpSerializer(serializers.ModelSerializer):
    """
    Сериализатор для регистрации нового пользователя.
    Проверяет корректность введенных данных и создает пользователя.
    """
    email = serializers.EmailField(
        required=True,
        max_length=254,
        validators=[EmailValidator()]
    )
    username = serializers.RegexField(r'^[\w.@+-]{1,150}$', required=True)

    class Meta:
        model = User
        fields = ("email", "username")

    def validate(self, data):
        """
        Проверяет корректность данных перед созданием пользователя.
        Генерирует ошибки, если имя пользователя или email уже существуют,
        или если имя пользователя запрещено.
        """
        errors = {}
        if data['username'].lower() == settings.NOT_ALLOWED_USERNAME:
            errors['username'] = _(
                'Использование имени пользователя "me" запрещено'
            )
        if not User.objects.filter(
            username=data['username'], email=data['email']
        ):

            if User.objects.filter(username=data['username']).exists():
                errors['username'] = errors.get(
                    'username', _(
                        "Пользователь с таким username уже существует."
                    )
                )

            if User.objects.filter(email=data['email']).exists():
                errors['email'] = _(
                    "Пользователь с таким email уже существует."
                )
        if errors:
            raise serializers.ValidationError(errors)
        return data

    def create(self, validated_data):
        """
        Создает нового пользователя на основе валидированных данных.
        Генерирует код подтверждения и отправляет его на email пользователя.
        """
        email = validated_data['email']
        username = validated_data['username']
        user, created = User.objects.get_or_create(
            username=username, email=email
        )
        if created:
            user.confirmation_code = default_token_generator.make_token(user)
            user.save()
        else:
            user.confirmation_code = default_token_generator.make_token(user)
            user.save(update_fields=['confirmation_code'])
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {user.confirmation_code}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return user


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
        username = data['username']
        confirmation_code = data['confirmation_code']
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise NotFound('Пользователь не найден')
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError('Неправильный код подтверждения')

        data['user'] = user
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

    class Meta:
        model = Review
        fields = ("id", "text", "author", "score", "pub_date")


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
    Позволяет создавать и обновлять информацию о пользователе.
    """
    email = serializers.EmailField(
        max_length=254,
        validators=[EmailValidator()]
    )
    username = serializers.RegexField(r'^[\w.@+-]{1,150}$', required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate(self, attrs):
        """
        Проверяет корректность введенных данных для пользователя.
        Убедитесь, что имя пользователя и email уникальны.
        Обрабатывает случаи обновления данных пользователя.
        """
        request = self.context.get('request')
        username = attrs.get('username')
        email = attrs.get('email')

        if request and request.method == 'PATCH':
            current_username = request.parser_context['kwargs'].get('username')
            current_user = User.objects.get(username=current_username)

            if username and username != current_user.username:
                if User.objects.filter(username=username).exists():
                    raise serializers.ValidationError({
                        "username": (
                            "Пользователь с таким username"
                            "уже существует."
                        )
                    })

            if email and email != current_user.email:
                if User.objects.filter(email=email).exists():
                    raise serializers.ValidationError({
                        "email": "Пользователь с таким email уже существует."
                    })

        else:
            if username and User.objects.filter(username=username).exists():
                raise serializers.ValidationError({
                    "username": "Пользователь с таким username уже существует."
                })

            if email and User.objects.filter(email=email).exists():
                raise serializers.ValidationError({
                    "email": "Пользователь с таким email уже существует."
                })

        return attrs


class UserMeSerializer(serializers.ModelSerializer):
    """
    Сериализатор для представления и обновления данных текущего пользователя.
    Позволяет пользователю изменять свои данные, но не изменять роль.
    """
    email = serializers.EmailField(
        max_length=254,
        validators=[EmailValidator()]
    )
    username = serializers.RegexField(r'^[\w.@+-]{1,150}$', required=True)

    class Meta:
        model = User
        fields = (
            'username', 'email', 'first_name', 'last_name', 'bio', 'role'
        )
        extra_kwargs = {
            'username': {'allow_blank': False},
            'email': {'allow_blank': False},
            'role': {'read_only': True}
        }
