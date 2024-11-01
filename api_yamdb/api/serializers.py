from django.core.mail import send_mail
from django.core.validators import EmailValidator
from rest_framework import serializers

from users.models import CustomUser
from .utils import generate_confirmation_code

from reviews.models import Category, Comment, Genre, Review, Title
from reviews.validators import validate_title_year


class SignUpSerializer(serializers.ModelSerializer):
    email = serializers.EmailField(validators=[EmailValidator])

    class Meta:
        model = CustomUser
        fields = ('email', 'username')

    def create(self, validated_data):
        user = CustomUser.objects.create_user(**validated_data)
        confirmation_code = generate_confirmation_code()
        user.confirmation_code = confirmation_code
        user.save()
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {confirmation_code}',
            from_email=None,
            recipient_list=[user.email],
            fail_silently=False,
        )
        return user


class AuthTokenSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=150)
    confirmation_code = serializers.CharField(max_length=16)

    def validate(self, attrs):
        username = attrs['username']
        confirmation_code = attrs['confirmation_code']
        try:
            user = CustomUser.objects.get(username=username)
        except CustomUser.DoesNotExist:
            raise serializers.ValidationError('Пользователь не найден')
        if user.confirmation_code != confirmation_code:
            raise serializers.ValidationError('Неправильный код подтверждения')
        return attrs


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
