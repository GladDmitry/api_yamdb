from django.conf import settings
from django.core.mail import send_mail
from django.core.validators import EmailValidator
from django.forms import ValidationError
from django.contrib.auth.tokens import default_token_generator
from rest_framework import serializers
from users.models import CustomUser
from .utils import generate_confirmation_code
from reviews.models import Category, Comment, Genre, Review, Title
from reviews.validators import validate_title_year
from users.models import User


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator])
    username = serializers.RegexField(r'^[\w.@+-]{1,150}$')

    class Meta:
        model = User
        fields = ("email", "username")

    def validate(self, data):
        if data['username'].lower() == settings.NOT_ALLOWED_USERNAME:
            raise ValidationError('Использование имени пользователя "me" запрещено')

            # Проверка, существует ли пользователь с таким username и email
        if not User.objects.filter(username=data['username'], email=data['email']):
            # Проверка на уникальность username
            if User.objects.filter(username=data['username']).exists():
                raise serializers.ValidationError("Пользователь с таким username уже существует.")

            # Проверка на уникальность email
            if User.objects.filter(email=data['email']).exists():
                raise serializers.ValidationError("Пользователь с таким email уже существует.")

        return data

    def create(self, validated_data):
        email = validated_data['email']
        username = validated_data['username']
        user, created = User.objects.get_or_create(username=username, email=email)
        if created:
            # Если пользователь создан, генерируем новый код подтверждения
            user.confirmation_code = default_token_generator.make_token(user)
            user.save()
        else:
            # Если пользователь уже существует, обновляем код подтверждения
            user.confirmation_code = default_token_generator.make_token(user)
            user.save(update_fields=['confirmation_code'])
        # Отправляем код подтверждения на почту
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {user.confirmation_code}',
            settings.DEFAULT_FROM_EMAIL,
            [email],
            fail_silently=False,
        )

        return user


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=50)

    def validate(self, data):
        username = data['username']
        confirmation_code = data['confirmation_code']
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError('Неправильный код подтверждения')
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
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio', 'role')
        extra_kwargs = {
            'username': {'required': True, 'allow_blank': False},
            'email': {'required': True, 'allow_blank': False},
        }

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("Пользователь с таким username уже существует.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("Пользователь с таким email уже существует.")
        return value


class UserMeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('username', 'email', 'first_name', 'last_name', 'bio')
        extra_kwargs = {
            'username': {'allow_blank': False},
            'email': {'allow_blank': False},
        }
