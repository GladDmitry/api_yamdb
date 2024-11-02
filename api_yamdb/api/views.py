from rest_framework import viewsets, status, filters
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated, IsAdminUser
from users.models import CustomUser
from .serializers import SignUpSerializer, AuthTokenSerializer
from django.core.exceptions import ValidationError
from django.db.models import Avg
from django_filters.rest_framework import DjangoFilterBackend
from django.shortcuts import get_object_or_404
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import serializers
from rest_framework.views import APIView
from users.models import User
from rest_framework.decorators import action
from rest_framework.filters import SearchFilter
from rest_framework.pagination import PageNumberPagination
from api.filters import FilterTitle
from api.mixins import ModelMixinSet
from api.permissions import (IsAdminUserOrReadOnly, 
                             IsAdminModeratorAuthorOrReadOnly,)
from api.serializers import (AuthTokenSerializer, CategorySerializer,
                             CommentSerializer, GenreSerializer,
                             SignUpSerializer, ReviewSerializer,
                             TitleReadSerializer, TitleWriteSerializer,
                             UserMeSerializer, UserSerializer)
from reviews.models import Category, Genre, Review, Title


class SignUpView(APIView):
    permission_classes = [AllowAny]
    serializer_class = SignUpSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        return Response({'email': user.email, 'username': user.username}, status=status.HTTP_201_CREATED)


class AuthTokenView(APIView):
    permission_classes = [AllowAny]
    serializer_class = AuthTokenSerializer

    def post(self, request):
        serializer = self.serializer_class(data=request.data)
        serializer.is_valid(raise_exception=True)
        username = serializer.validated_data['username']
        user = CustomUser.objects.get(username=username)
        refresh = RefreshToken.for_user(user)
        return Response({'token': str(refresh.access_token)}, status=status.HTTP_200_OK)


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
    #    queryset = Title.objects.annotate(
    #        rating=Avg('reviews__score')
    #    ).all()
    permission_classes = (IsAdminUserOrReadOnly,)
    filter_backends = (DjangoFilterBackend,)
    filterset_class = FilterTitle
    http_method_names = ['get', 'post', 'patch', 'delete',]

    def get_serializer_class(self):
        if self.action in ('list', 'retrieve'):
            return TitleReadSerializer
        return TitleWriteSerializer


class UsersViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    lookup_field = 'username'
    filter_backends = [SearchFilter]
    search_fields = ['username']
    pagination_class = PageNumberPagination
    http_method_names = ('get', 'post', 'patch', 'delete',)

    def get_permissions(self):
        if self.action == 'me':
            return [IsAuthenticated()]
        return [IsAdminUser()]

    def get_serializer_class(self):
        if self.action == 'me':
            return UserMeSerializer
        return UserSerializer
      
    @action(detail=False, methods=['get', 'patch'], permission_classes=[IsAuthenticated])
    def me(self, request):
        user = request.user
        if request.method == 'GET':
            serializer = self.get_serializer(user)
            return Response(serializer.data)
        elif request.method == 'PATCH':
            serializer = self.get_serializer(user, data=request.data, partial=True)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            return Response(serializer.data)
          

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
