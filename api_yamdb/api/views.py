from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from django.conf import settings
from django.core.mail import send_mail
from django.db import IntegrityError

from api.filters import FilterTitle
from api.mixins import ModelMixinSet
from api.permissions import (IsAuthenticatedAdminOrReadOnly,
                             IsAuthenticatedAdminOrStaff,
                             IsAdminModeratorAuthorOrReadOnly,
                             IsOwner)
from api.serializers import (AuthTokenSerializer, CategorySerializer,
                             CommentSerializer, GenreSerializer,
                             ReviewSerializer, SignUpSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             UserSerializer)

from reviews.models import Category, Genre, Review, Title
from .pagination import CustomPageNumberPagination
from .serializers import SignUpSerializer, AuthTokenSerializer
from users.models import User, UserProfile


class SignUpView(APIView):
    """
    Представление для регистрации нового пользователя.
    Доступно для всех пользователей.
    """
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request):
        """
        Создает нового пользователя на основе переданных данных.
        В случае успеха возвращает email и имя пользователя.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        confirmation_code = user.confirmation_code
        send_mail(
            'Код подтверждения',
            f'Ваш код подтверждения: {confirmation_code}',
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )
        return Response(
            {'email': user.email, 'username': user.username},
            status=status.HTTP_200_OK
        )


class AuthTokenView(APIView):
    """
    Представление для получения токена аутентификации.
    Доступно для всех пользователей.
    """
    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer

    def post(self, request):
        """
        Генерирует токен для аутентифицированного пользователя.
        В случае успеха возвращает токен.
        """
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.validated_data['user']
        refresh = RefreshToken.for_user(user)
        return Response(
            {'token': str(refresh.access_token)},
            status=status.HTTP_200_OK
        )


class CategoryViewSet(ModelMixinSet):
    queryset = Category.objects.all()
    serializer_class = CategorySerializer
    permission_classes = (IsAuthenticatedAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(ModelMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAuthenticatedAdminOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).order_by('id')
    permission_classes = (IsAuthenticatedAdminOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterTitle
    http_method_names = ['get', 'post', 'patch', 'delete', ]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class UsersViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с пользователями.
    Доступно для администраторов и для аутентифицированных пользователей.
    """
    queryset = UserProfile.objects.all()
    lookup_field = 'username'
    filter_backends = [SearchFilter]
    search_fields = ['username']
    pagination_class = CustomPageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete',)
    permission_classes = [IsAuthenticatedAdminOrStaff]
    serializer_class = UserSerializer

    @action(detail=False,
            methods=['get', 'post', 'patch',
                     'delete', 'put', 'options', 'head'],
            permission_classes=[IsOwner])
    def me(self, request):
        """
        Позволяет пользователю получить или обновить свои данные.
        Доступно только для аутентифицированных пользователей.
        """
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            data = request.data.copy()
            data.pop('role', None)
            serializer = self.get_serializer(
                user, data=data, partial=True
            )
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
        else:
            return Response({'detail': 'Метод не разрешен.'},
                            status=status.HTTP_405_METHOD_NOT_ALLOWED)


class ReviewViewSet(viewsets.ModelViewSet):
    serializer_class = ReviewSerializer
    permission_classes = (IsAdminModeratorAuthorOrReadOnly,)
    http_method_names = ["get", "post", "patch", "delete", ]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        return title.reviews.all()

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAdminModeratorAuthorOrReadOnly, )
    http_method_names = ["get", "post", "patch", "delete", ]

    def get_permissions(self):
        if self.action in ["list", "retrieve"]:
            return [AllowAny()]
        return super().get_permissions()

    def perform_create(self, serializer):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get("review_id"),
            title__id=self.kwargs.get("title_id")
        )
        serializer.save(author=self.request.user, review=review)

    def get_queryset(self):
        review = get_object_or_404(
            Review,
            id=self.kwargs.get("review_id"),
            title__id=self.kwargs.get("title_id")
        )
        return review.comments.all()
