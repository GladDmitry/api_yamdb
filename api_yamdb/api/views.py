from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny
from users.models import CustomUser
from .serializers import SignUpSerializer, AuthTokenSerializer
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework.views import APIView
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from api.filters import FilterTitle
from api.mixins import ModelMixinSet
from api.permissions import (IsAdminUserOrReadOnly,
                             IsAdminOrSuperUser,
                             IsAdminModeratorAuthorOrReadOnly,
                             IsAuthenticatedUser)
from api.serializers import (AuthTokenSerializer, CategorySerializer,
                             CommentSerializer, GenreSerializer,
                             SignUpSerializer, ReviewSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             UserMeSerializer, UserSerializer)
from reviews.models import Category, Genre, Review, Title
from .pagination import CustomPageNumberPagination


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
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class GenreViewSet(ModelMixinSet):
    queryset = Genre.objects.all()
    serializer_class = GenreSerializer
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (filters.SearchFilter,)
    search_fields = ('name',)
    lookup_field = 'slug'


class TitleViewSet(viewsets.ModelViewSet):
    queryset = Title.objects.annotate(
        rating=Avg('reviews__score')
    ).all()
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterTitle
    http_method_names = ['get', 'post', 'patch', 'delete',]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class UsersViewSet(viewsets.ModelViewSet):
    """
    Представление для работы с пользователями.
    Доступно для администраторов и для аутентифицированных пользователей.
    """
    queryset = CustomUser.objects.all()
    lookup_field = 'username'
    filter_backends = [SearchFilter]
    search_fields = ['username']
    pagination_class = CustomPageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def get_permissions(self):
        """
        Возвращает разрешения для действий в зависимости от типа запроса.
        Для действия 'me' требуется аутентификация,
        для остальных - административные права.
        """
        if self.action == 'me':
            return [IsAuthenticatedUser()]
        return [IsAdminOrSuperUser()]

    def get_serializer_class(self):
        """
        Возвращает соответствующий сериализатор в зависимости от действия.
        Для действия 'me' используется UserMeSerializer,
        для остальных - UserSerializer.
        """
        if self.action == 'me':
            return UserMeSerializer
        return UserSerializer

    def create(self, request, *args, **kwargs):
        """
        Создает нового пользователя на основе переданных данных.
        В случае успеха возвращает данные созданного пользователя.
        """
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        return Response(serializer.data, status=status.HTTP_201_CREATED)

    @action(detail=False,
            methods=['get', 'post', 'patch',
                     'delete', 'put', 'options', 'head'],
            permission_classes=[IsAuthenticatedUser])
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
            serializer = self.get_serializer(
                user, data=request.data, partial=True
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
    http_method_names = ['get', 'post', 'patch', 'delete',]

    def get_queryset(self):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        return title.reviews.all()

    def perform_create(self, serializer):
        title = get_object_or_404(Title, id=self.kwargs.get("title_id"))
        serializer.save(author=self.request.user, title=title)


class CommentsViewSet(viewsets.ModelViewSet):
    serializer_class = CommentSerializer
    permission_classes = (IsAdminModeratorAuthorOrReadOnly, )
    http_method_names = ['get', 'post', 'patch', 'delete',]

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
