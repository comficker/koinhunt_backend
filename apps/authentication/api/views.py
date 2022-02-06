from django.db.models import Q, Count
from rest_framework.response import Response
from rest_framework import viewsets
from rest_framework.filters import OrderingFilter
from apps.base import pagination
from . import serializers
from apps.project import models


class WalletViewSet(viewsets.ModelViewSet):
    models = models.Wallet
    queryset = models.objects.order_by('-id')
    serializer_class = serializers.WalletSerializer
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter]
    lookup_field = 'pk'

    def list(self, request, *args, **kwargs):
        q = Q()
        if request.GET.get("type"):
            if request.GET.get("type") == "validator":
                self.queryset = self.queryset \
                    .select_related("validates") \
                    .annotate(total=Count("validates__pk")) \
                    .order_by("-total")
            elif request.GET.get("type") == "hunter":
                self.queryset = self.queryset\
                    .select_related("hunted_tokens")\
                    .annotate(total=Count("hunted_tokens__pk"))\
                    .order_by("-total")
        queryset = self.filter_queryset(self.queryset.filter(q))
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
