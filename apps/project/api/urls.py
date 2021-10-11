from . import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import include, url

router = DefaultRouter()
router.register(r'tokens', views.TokenViewSet)
router.register(r'partners', views.PartnerViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'terms', views.TermViewSet)
router.register(r'projects', views.ProjectViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'home/$', views.home),
    url(r'projects/(?P<id_string>[-\w]+)/vote/$', views.token_vote),
]
