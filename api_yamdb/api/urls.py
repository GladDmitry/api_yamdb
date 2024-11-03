from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (AuthTokenView, CategoryViewSet, CommentsViewSet,
                       GenreViewSet, ReviewViewSet, SignUpView,
                       TitleViewSet, UsersViewSet)


router = DefaultRouter()
router.register('categories', CategoryViewSet, basename='categories')
router.register('genres', GenreViewSet, basename='genres')
router.register('titles', TitleViewSet, basename='titles')
router.register(r"users", UsersViewSet)
router.register(
    r'titles/(?P<title_id>\d+)/reviews',
    ReviewViewSet,
    basename='reviews'
)
router.register(
    r'titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments',
    CommentsViewSet,
    basename='comments'
)


urlpatterns = [
    path('v1/auth/signup/', SignUpView.as_view(), name='signup'),
    path("v1/auth/token/",
         AuthTokenView.as_view(), name='token_obtain_pair'),
    path("v1/", include(router.urls)),
]
