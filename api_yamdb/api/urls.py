from django.urls import include, path
from rest_framework.routers import DefaultRouter
from api.views import (AuthTokenViewSet, CategoryViewSet, CommentsViewSet,
                       GenreViewSet, ReviewViewSet, SignUpViewSet,
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
    path("v1/auth/signup/", SignUpViewSet.as_view({'post': 'create'})),
    path("v1/auth/token/",
         AuthTokenViewSet.as_view({'post': 'create'}), name='token_obtain_pair'),
    path("v1/", include(router.urls)),
]

