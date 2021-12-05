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


def save_extra(instance, request):
    raw_events = request.data.get("events", [])
    raw_tokens = request.data.get("tokens", [])
    raw_media = request.data.get("rawMedia")
    for raw_launch in raw_events:
        if raw_launch.get("partner") is None or raw_launch.get("id"):
            continue
        partner = models.Partner.objects.get(pk=raw_launch.get("partner"))
        models.Event.objects.create(
            project=instance,
            partner=partner,
            event_name=raw_launch.get("event_name"),
            event_date_start=raw_launch.get("event_date_start"),
            event_date_end=raw_launch.get("event_date_end"),
        )
    for raw_token in raw_tokens:
        if raw_token.get("id"):
            continue
        chain = models.Term.objects.get(pk=raw_token.get("chain"))
        models.Token.objects.get_or_create(
            chain=chain,
            address=raw_token.get("address"),
            defaults={
                "project": instance,
                "decimal": raw_token.get("decimal"),
                "symbol": raw_token.get("symbol"),
                "total_supply": raw_token.get("total_supply"),
                "circulating_supply": raw_token.get("circulating_supply"),
                "meta": raw_token.get("meta")
            }
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
        q = Q(db_status=1)
        if request.GET.get("taxonomy"):
            q = q & Q(taxonomy=request.GET.get("taxonomy"))
        queryset = self.filter_queryset(self.get_queryset().filter(q))

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        name = request.data.get("name")
        taxonomy = request.data.get("taxonomy")
        instance, _ = models.Term.objects.get_or_create(
            name=name,
            taxonomy=taxonomy
        )
        return Response(serializers.TermSerializer(instance).data)

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

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.ProjectDetailSerializer
        self.queryset = models.Project.objects.order_by('-id') \
            .prefetch_related("events").prefetch_related("events__partner") \
            .prefetch_related("tokens").prefetch_related("tokens__chain") \
            .select_related("hunter").select_related("media") \
            .prefetch_related("terms")
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        q = Q(db_status=1)
        if request.GET.get("terms__taxonomy"):
            q = q & Q(terms__taxonomy=request.GET.get("terms__taxonomy"))
        if request.GET.get("terms__id_string"):
            q = q & Q(terms__id_string=request.GET.get("terms__id_string"))
        queryset = self.filter_queryset(
            models.Project.objects
                .prefetch_related("media")
                .prefetch_related("terms")
                .prefetch_related("hunter")
                .prefetch_related("events")
                .prefetch_related("events__partner")
                .filter(q)
                .order_by('-calculated_score')
        )

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
        instance = models.Project.objects.get(id=serializer.data.get("id"))
        save_extra(instance, request)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        instance = self.get_object()
        if request.user.is_authenticated and request.user.is_staff or request.user is instance.hunter:
            partial = kwargs.pop('partial', True)
            serializer = self.get_serializer(instance, data=request.data, partial=partial)
            serializer.is_valid(raise_exception=True)
            serializer.save()
            if getattr(instance, '_prefetched_objects_cache', None):
                instance._prefetched_objects_cache = {}
            instance = self.get_object()
            save_extra(instance, request)
            return Response(serializer.data)
        return Response(status=status.HTTP_401_UNAUTHORIZED)

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
