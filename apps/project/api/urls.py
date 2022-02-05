from . import views
from rest_framework.routers import DefaultRouter
from django.conf.urls import include, url

router = DefaultRouter()
router.register(r'tokens', views.TokenViewSet)
router.register(r'events', views.EventViewSet)
router.register(r'terms', views.TermViewSet)
router.register(r'projects', views.ProjectViewSet)
router.register(r'collections', views.CollectionViewSet)

urlpatterns = [
    url(r'^', include(router.urls)),
    url(r'projects/(?P<id_string>[-\w]+)/vote/$', views.project_vote),
    url(r'collections/(?P<pk>[-\w]+)/add/$', views.collection_add),
]
