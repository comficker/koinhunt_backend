"""koinhunt_back URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/3.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.conf import settings
from django.conf.urls.static import static
from django.conf.urls import include, url
from django.urls import re_path
from . import view

urlpatterns = [
    url(r'^v1/media/', include(('apps.media.api.urls', 'api_media'))),
    url(r'^v1/project/', include(('apps.project.api.urls', 'api_coin'))),
    url(r'^v1/auth/', include(('apps.authentication.api.urls', 'api_auth'))),

    re_path(r'^main-sitemap.xsl', view.sitemap_style),
    re_path(r'^sitemap_index.xml', view.sitemap_index),
    url(r'(?P<flag>[-\w.]+)-sitemap.xml$', view.sitemap_detail),
] + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

