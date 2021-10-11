from django.db.models import Q
import base64

from django.core.files.base import ContentFile
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets, permissions
from rest_framework.filters import OrderingFilter, SearchFilter
from apps.base import pagination
from . import serializers
from apps.project import models
from apps.media.models import Media

CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)


class TermViewSet(viewsets.ModelViewSet):
    models = models.Term
    queryset = models.objects.order_by('-created')
    serializer_class = serializers.TermSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'slug'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class PartnerViewSet(viewsets.ModelViewSet):
    models = models.Partner
    queryset = models.objects.order_by('-created')
    serializer_class = serializers.PartnerSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'slug'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class ProjectViewSet(viewsets.ModelViewSet):
    models = models.Project
    queryset = models.objects.order_by('-calculated_score')
    serializer_class = serializers.ProjectSerializer
    permission_classes = permissions.AllowAny,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'id_string'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        raw_events = request.data.get("events", [])
        raw_media = request.data.get("rawMedia")
        instance = models.Project.objects.get(id=serializer.data.get("id"))
        for raw_launch in raw_events:
            partner = models.Partner.objects.get(pk=raw_launch['partner'])
            models.Event.objects.create(
                project=instance,
                partner=partner,
                date_start=raw_launch['date']
            )
        if raw_media:
            fm, img_str = raw_media.split(';base64,')
            ext = fm.split('/')[-1]
            file_name = instance.id_string + "." + ext
            data = ContentFile(base64.b64decode(img_str), name=file_name)
            media = Media.objects.create(
                title=request.data.get("name"),
                path=data,
                user=request.user if request.user.is_authenticated else None
            )
            instance.media = media
            instance.save()
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class TokenViewSet(viewsets.ModelViewSet):
    models = models.Token
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.TokenSerializer
    permission_classes = permissions.AllowAny,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['token_address', 'token_symbol']
    lookup_field = 'address'

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class EventViewSet(viewsets.ModelViewSet):
    models = models.Event
    queryset = models.objects.order_by('event_date_start')
    serializer_class = serializers.EventSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        q = Q()
        if request.GET.get("project"):
            q = q & Q(project_id=request.GET.get("project"))
        if request.GET.get("event_name"):
            q = q & Q(event_name=request.GET.get("event_name"))
        queryset = self.filter_queryset(models.Event.objects.filter(q).order_by('event_date_start'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        pass

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


@api_view(['GET'])
def home(request):
    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def token_vote(request, id_string):
    return Response({}, status=status.HTTP_200_OK)
