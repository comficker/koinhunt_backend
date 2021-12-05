from django.urls import path, re_path
from apps.authentication.api import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import include, url
from rest_framework_jwt.views import refresh_jwt_token, obtain_jwt_token

router = DefaultRouter()
router.register(r'users', views.UserViewSet)

urlpatterns = [
    path('users/me/', views.UserExt.get_request_user),
    url(r'^', include(router.urls)),
    path('blockchain/', views.auth),
]
