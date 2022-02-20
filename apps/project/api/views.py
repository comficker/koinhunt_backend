import os
import base64
import json
from django.utils import timezone
from django.db.models import Q, Case, When, IntegerField, DurationField
from django.db.models import Subquery, OuterRef, F, Prefetch
from django.core.files.base import ContentFile
from django.conf import settings
from django.core.cache.backends.base import DEFAULT_TIMEOUT
from django.contrib.contenttypes.models import ContentType
from rest_framework import status
from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter, SearchFilter
from apps.base import pagination
from apps.project import models
from apps.media.models import Media
from eth_account.messages import defunct_hash_message
from web3 import Web3
from utils.wallets import operators
from . import serializers

w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
CACHE_TTL = getattr(settings, 'CACHE_TTL', DEFAULT_TIMEOUT)
REWARD_BASE = float(os.getenv("REWARD_BASE", "0"))


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
        models.Token.objects.get_or_create(
            chain_id=raw_token.get("chain_id"),
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
        media = Media(
            title=request.data.get("name"),
            path=data,
        )
        media.path.save(file_name, data)
        instance.media = media
    instance.save()


class TermViewSet(viewsets.ModelViewSet):
    models = models.Term
    queryset = models.objects.order_by('-created')
    serializer_class = serializers.TermSerializer
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
    queryset = models.objects.order_by('-score_calculated')
    serializer_class = serializers.ProjectSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['name', 'description']
    lookup_field = 'id_string'

    def retrieve(self, request, *args, **kwargs):
        self.serializer_class = serializers.ProjectSerializerDetail
        self.queryset = models.Project.objects.order_by('-id') \
            .prefetch_related("tokens") \
            .select_related("wallet").select_related("media") \
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
        now = timezone.now()
        qs = models.Project.objects \
            .prefetch_related("collections") \
            .prefetch_related("media") \
            .prefetch_related("terms") \
            .prefetch_related("wallet")

        q = Q(db_status=1, wallet__isnull=False)
        if request.GET.get("validating") != "true":
            q = q & Q(validation_score__gte=F("init_power_target"))
        elif request.GET.get("validating") != "false":
            q = q & Q(validation_score__lt=F("init_power_target"))
        if request.GET.get("terms__taxonomy"):
            q = q & Q(terms__taxonomy=request.GET.get("terms__taxonomy"))
        if request.GET.get("terms__id_string"):
            q = q & Q(terms__id_string=request.GET.get("terms__id_string"))
        if request.GET.get("collection"):
            q = q & Q(collections__id=request.GET.get("collection"))
        if request.GET.get("hunter"):
            q = q & Q(wallet_id=request.GET.get("hunter"))
        if request.GET.get("validator"):
            ct = ContentType.objects.get(model="project", app_label="project")
            wl_qs = models.Validate.objects.filter(
                wallet_id=request.GET.get("validator"),
                target_content_type=ct
            ).values_list("target_object_id")
            q = q & Q(id__in=list(map(lambda x: x[0], wl_qs)))
        if request.GET.get("terms"):
            q = q & Q(terms__in=request.GET.get("terms").split(","))

        # =========== Starting query
        ev_qs = models.Event.objects.annotate(
            time_diff=Case(
                When(event_date_start__gte=now, then=F('event_date_start') - now),
                When(event_date_start__lt=now, then=now - F('event_date_start')),
                output_field=DurationField(),
            )).order_by('time_diff')
        queryset = self.filter_queryset(
            qs \
                .filter(q).annotate(event_date_start=Subquery(ev_qs.values("event_date_start")[:1])) \
                .prefetch_related(
                Prefetch(
                    "project_events",
                    queryset=ev_qs,
                    to_attr='active_prices'
                )
            ).order_by('-event_date_start', '-score_calculated')
        )

        # =========== Making instance
        instance = None
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
        if request.wallet is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.data["wallet"] = request.wallet.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        instance = models.Project.objects.get(id=serializer.data.get("id"))
        save_extra(instance, request)
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
        if request.wallet is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.data["wallet"] = request.wallet.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
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
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        now = timezone.now()
        q = Q()
        if request.GET.get("validating") == "true":
            q = q & (Q(event_date_start__gt=now) | Q(event_date_start__isnull=True))
            q = q & Q(verified=False)
        else:
            q = q & Q(validation_score__gte=REWARD_BASE * 100)
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
        if request.GET.get("is_all") != "true":
            queryset = queryset[:1]
        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True)
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, context={
            'request': request,
        })
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        if request.wallet is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.data["wallet"] = request.wallet.id
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
        if request.wallet is None:
            return Response(status=status.HTTP_401_UNAUTHORIZED)
        request.data["wallet"] = request.wallet.id
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        self.perform_create(serializer)
        headers = self.get_success_headers(serializer.data)
        return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)

    def update(self, request, *args, **kwargs):
        pass

    def destroy(self, request, *args, **kwargs):
        pass


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


@api_view(['GET', 'POST'])
def contribute(request):
    target_type = request.GET.get("target_type")
    target_id = request.GET.get("target_id")
    content_type = ContentType.objects.get(app_label='project', model=target_type)
    if request.method == "GET":
        return Response(
            serializers.ContributeSerializerSimple(models.Contribute.objects.filter(
                target_content_type=target_type,
                target_object_id=target_id
            ), many=True).data
        )
    else:
        for key in request.body.keys():
            if not models.Contribute.objects.filter(
                target_content_type=content_type,
                target_object_id=target_id,
                field=key,
                verified=True,
            ).exists():
                models.Contribute.objects.get_or_create(
                    wallet=request.wallet,
                    target_content_type=content_type,
                    target_object_id=target_id,
                    field=key,
                    data=request.body.get(key)
                )


@api_view(['GET', 'POST'])
def validate(request):
    contrib = request.GET.get("contribute")
    if request.method == "GET":
        return Response(
            serializers.ValidateSerializerSimple(models.Validate.objects.filter(
                contribute_id=contrib
            ), many=True).data
        )
    else:
        # Tối đa số dự án đc hunt 1 ngày. Khoảng thời gian thời gian tối thiểu giữa các lần hunt hoặc validate;
        sign_mess = request.data.get("message")
        signature = request.data.get("signature")
        message_hash = defunct_hash_message(text=sign_mess)
        address = w3.eth.account.recoverHash(message_hash, signature=signature)
        decoded = base64.b64decode(sign_mess)
        m_json = json.loads(decoded)
        power = 1
        if address == request.wallet.address and m_json.get("contrib") and m_json.get("timestamp"):
            if address in operators.keys():
                for key in operators.keys():
                    operator_wallet, _ = models.Wallet.objects.get_or_create(
                        address=key,
                        chain="binance-smart-chain"
                    )
                    models.Validate.objects.get_or_create(
                        wallet=operator_wallet,
                        contribute_id=m_json.get("contrib"),
                        nft_id=m_json.get("nft") if m_json.get("nft") else None,
                        defaults={
                            "power": 500
                        }
                    )
            else:
                models.Validate.objects.get_or_create(
                    wallet=request.wallet,
                    contribute_id=m_json.get("contrib"),
                    nft_id=m_json.get("nft") if m_json.get("nft") else None,
                    defaults={
                        "power": power
                    }
                )
            return Response({})
