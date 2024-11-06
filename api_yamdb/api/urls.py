from django.urls import include, path
from rest_framework.routers import DefaultRouter

from api.views import (
    AuthTokenView,
    CategoryViewSet,
    CommentsViewSet,
    GenreViewSet,
    ReviewViewSet,
    SignUpView,
    TitleViewSet,
    UsersViewSet,
)
from api_yamdb.settings import API_VERSION


router_v1 = DefaultRouter()
router_v1.register("categories", CategoryViewSet, basename="categories")
router_v1.register("genres", GenreViewSet, basename="genres")
router_v1.register("titles", TitleViewSet, basename="titles")
router_v1.register(r"users", UsersViewSet)
router_v1.register(r"titles/(?P<title_id>\d+)/reviews",
                   ReviewViewSet,
                   basename="reviews")
router_v1.register(
    r"titles/(?P<title_id>\d+)/reviews/(?P<review_id>\d+)/comments",
    CommentsViewSet,
    basename="comments",
)


urlpatterns = [
    path(f'{API_VERSION}/auth/signup/', SignUpView.as_view(), name="signup"),
    path(f'{API_VERSION}/auth/token/',
         AuthTokenView.as_view(),
         name="token_obtain_pair"),
    path(f'{API_VERSION}/', include(router_v1.urls)),
]
