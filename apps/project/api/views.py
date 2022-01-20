import base64
import datetime
from django.utils import timezone
from django.db.models import Q, Case, When, IntegerField, DurationField
from django.db.models import Subquery, OuterRef, F
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
    old_events = instance.target_events.all().values_list("id", flat=True)
    for raw_launch in raw_events:
        if raw_launch.get("id"):
            if raw_launch.get("id") not in old_events:
                event = models.Event.objects.get(pk=raw_launch.get("id"))
                event.db_status = -1
                event.save()
        else:
            event = models.Event.objects.create(
                project=instance,
                event_name=raw_launch.get("event_name"),
                event_date_start=raw_launch.get("event_date_start"),
                event_date_end=raw_launch.get("event_date_end"),
                name=raw_launch.get("name"),
                description=raw_launch.get("description")
            )
            for target_id in raw_launch.get("targets", []):
                target = models.Project.objects.filter(pk=target_id).first()
                event.targets.add(target)
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
        if request.GET.get("id_string"):
            q = q & Q(id_string=request.GET.get("id_string"))
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
        self.serializer_class = serializers.ProjectSerializerDetail
        self.queryset = models.Project.objects.order_by('-id') \
            .prefetch_related("tokens").prefetch_related("tokens__chain") \
            .select_related("hunter").select_related("media") \
            .prefetch_related("terms")
        instance = self.get_object()
        serializer = self.get_serializer(
            instance,
            context={
                'request': request,
                'show_collection': True
            })
        return Response(serializer.data)

    def list(self, request, *args, **kwargs):
        qs = models.Project.objects \
            .prefetch_related("collections") \
            .prefetch_related("media") \
            .prefetch_related("terms") \
            .prefetch_related("hunter")

        ev_qs = models.Event.objects.filter(
            project=OuterRef('pk'),
            event_date_start__gte=timezone.now()
        )
        instance = None
        q = Q(db_status=1)
        if request.GET.get("validated") != "false":
            q = q & Q(validation_score__gte=1000)
        if request.GET.get("terms__taxonomy"):
            q = q & Q(terms__taxonomy=request.GET.get("terms__taxonomy"))
        if request.GET.get("terms__id_string"):
            q = q & Q(terms__id_string=request.GET.get("terms__id_string"))
        if request.GET.get("collection"):
            q = q & Q(collections__id=request.GET.get("collection"))
        queryset = self.filter_queryset(
            qs
                .filter(q)
                .annotate(event=Subquery(ev_qs.values("event_date_start")[:1]))
                .order_by('event', '-calculated_score')
        )
        # ===========
        if request.GET.get("terms__taxonomy") and request.GET.get("terms__id_string"):
            instance = serializers.TermSerializer(models.Term.objects.get(
                taxonomy=request.GET.get("terms__taxonomy"),
                id_string=request.GET.get("terms__id_string")
            )).data
        if request.GET.get("collection"):
            instance = serializers.CollectionSerializer(
                models.Collection.objects.get(id=request.GET.get("collection"))
            ).data
        # ===========
        page = self.paginate_queryset(queryset)
        if page is not None:
            setattr(self.paginator, 'instance', instance)
            serializer = self.get_serializer(
                page,
                many=True,
                context={
                    'request': request,
                    'show_collection': True
                }
            )
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={'request': request})
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
        if request.user.is_authenticated and (request.user.is_staff or request.user is instance.hunter):
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
        serializer.save(
            hunter=self.request.user
        )
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class EventViewSet(viewsets.ModelViewSet):
    models = models.Event
    queryset = models.objects.order_by('-event_date_start')
    serializer_class = serializers.EventSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        now = timezone.now()
        q = Q()
        if request.GET.get("project"):
            q = q & Q(project_id=request.GET.get("project"))
        if request.GET.get("event_name"):
            q = q & Q(event_name=request.GET.get("event_name"))
        queryset = self.filter_queryset(
            models.Event.objects.filter(q).annotate(
                relevance=Case(
                    When(event_date_start__gte=now, then=1),
                    When(event_date_start__lt=now, then=2),
                    output_field=IntegerField(),
                )).annotate(
                time_diff=Case(
                    When(event_date_start__gte=now, then=F('event_date_start') - now),
                    When(event_date_start__lt=now, then=now - F('event_date_start')),
                    output_field=DurationField(),
                )).order_by('relevance', 'time_diff')
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
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


class CollectionViewSet(viewsets.ModelViewSet):
    models = models.Collection
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.CollectionSerializer
    permission_classes = permissions.IsAuthenticatedOrReadOnly,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        q = Q()
        if request.GET.get("user"):
            q = q & Q(user_id=request.GET.get("user"))
        queryset = self.filter_queryset(models.Collection.objects.filter(q).order_by('-id'))
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True)
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        request.data["user"] = request.user.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop('partial', True)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        if request.user.id == instance.user.id:
            serializer.save()
        else:
            # Contribute
            pass
        if getattr(instance, '_prefetched_objects_cache', None):
            # If 'prefetch_related' has been applied to a queryset, we need to
            # forcibly invalidate the prefetch cache on the instance.
            instance._prefetched_objects_cache = {}

        return Response(serializer.data)

    def destroy(self, request, *args, **kwargs):
        pass


@api_view(['GET'])
def home(request):
    return Response({}, status=status.HTTP_200_OK)


@api_view(['GET', 'POST'])
def project_vote(request, id_string):
    project = models.Project.objects.get(id_string=id_string)
    is_voted = False
    if request.method == "POST":
        if request.user.is_authenticated:
            is_voted = models.Vote.objects.filter(user=request.user, project=project).first()
            if is_voted:
                is_voted.delete()
                is_voted = False
            else:
                models.Vote.objects.create(user=request.user, project=project)
                is_voted = True
    return Response({
        "total": project.votes.count(),
        "is_voted": is_voted
    }, status=status.HTTP_200_OK)


@api_view(['POST'])
def collection_add(request, pk):
    col = models.Collection.objects.get(pk=pk)
    try:
        project = models.Project.objects.get(pk=request.data.get("project"))
        if project in col.projects.all():
            flag = False
            col.projects.remove(project)
        else:
            col.projects.add(project)
            flag = True
        return Response(flag, status=status.HTTP_200_OK)
    except Exception as e:
        print(e)
        return Response(status=status.HTTP_400_BAD_REQUEST)
