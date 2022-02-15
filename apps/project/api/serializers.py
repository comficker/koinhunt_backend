from django.utils import timezone
from django.db.models import Case, When, IntegerField, DurationField
from django.db.models import F
from apps.project import models
from rest_framework import serializers
from apps.media.api.serializers import MediaSerializer
from apps.authentication.api.serializers import WalletSerializer


class TermSerializer(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)

    class Meta:
        model = models.Term
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["media"] = MediaSerializer()
        return super(TermSerializer, self).to_representation(instance)


class ProjectSerializer(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)
    collections = serializers.SerializerMethodField()

    class Meta:
        model = models.Project
        fields = '__all__'
        extra_fields = ["collections"]

    def to_representation(self, instance):
        self.fields["terms"] = TermSerializer(many=True)
        self.fields["media"] = MediaSerializer()
        self.fields["wallet"] = WalletSerializer()
        self.fields["main_token"] = TokenSerializer()
        return super(ProjectSerializer, self).to_representation(instance)

    def get_events(self, instance):
        return EventSerializerSimple(instance.project_events.all(), many=True).data

    def get_collections(self, instance):
        request = self.context.get("request")
        if request and request.wallet and self.context.get("show_collection"):
            return CollectionSerializerSimple(
                instance.collections.filter(wallet=request.wallet),
                many=True
            ).data
        return []

    def get_field_names(self, declared_fields, info):
        expanded_fields = super(ProjectSerializer, self).get_field_names(declared_fields, info)
        if getattr(self.Meta, 'extra_fields', None) and len(self.Meta.extra_fields) > 0:
            return expanded_fields + list(self.Meta.extra_fields)
        else:
            return expanded_fields


class ProjectSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Project
        fields = '__all__'


class ProjectSerializerDetail(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)
    events = serializers.SerializerMethodField()
    vote = serializers.SerializerMethodField()
    collections = serializers.SerializerMethodField()

    class Meta:
        model = models.Project
        fields = '__all__'
        extra_fields = ["events", "vote", "collections"]

    def to_representation(self, instance):
        self.fields["terms"] = TermSerializer(many=True)
        self.fields["media"] = MediaSerializer()
        self.fields["wallet"] = WalletSerializer()
        self.fields["tokens"] = TokenSerializer(many=True)
        return super(ProjectSerializerDetail, self).to_representation(instance)

    def get_events(self, instance):
        now = timezone.now()
        return EventSerializerSimple(
            instance.project_events.filter(validation_score__gte=500).annotate(
                relevance=Case(
                    When(event_date_start__gte=now, then=1),
                    When(event_date_start__lt=now, then=2),
                    output_field=IntegerField(),
                )).annotate(
                time_diff=Case(
                    When(event_date_start__gte=now, then=F('event_date_start') - now),
                    When(event_date_start__lt=now, then=now - F('event_date_start')),
                    output_field=DurationField(),
                )).order_by('relevance', 'time_diff'),
            many=True
        ).data

    def get_vote(self, instance):
        data = {
            "total": 0,
            "is_voted": False
        }
        return data

    def get_collections(self, instance):
        request = self.context.get("request")
        if request and request.wallet and self.context.get("show_collection"):
            return CollectionSerializerSimple(
                instance.collections.filter(wallet=request.wallet),
                many=True
            ).data
        return []

    def get_field_names(self, declared_fields, info):
        expanded_fields = super(ProjectSerializerDetail, self).get_field_names(declared_fields, info)
        if getattr(self.Meta, 'extra_fields', None) and len(self.Meta.extra_fields) > 0:
            return expanded_fields + list(self.Meta.extra_fields)
        else:
            return expanded_fields


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Token
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        return super(TokenSerializer, self).to_representation(instance)


class TokenSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Token
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        return super(TokenSerializerSimple, self).to_representation(instance)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["targets"] = ProjectSerializer(many=True)
        self.fields["project"] = ProjectSerializer()
        return super(EventSerializer, self).to_representation(instance)


class EventSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["project"] = ProjectSerializerSimple()
        self.fields["targets"] = ProjectSerializerSimple(many=True)
        return super(EventSerializerSimple, self).to_representation(instance)


class CollectionSerializer(serializers.ModelSerializer):
    total = serializers.SerializerMethodField()

    class Meta:
        model = models.Collection
        fields = '__all__'
        extra_fields = ["total"]

    def to_representation(self, instance):
        self.fields["wallet"] = WalletSerializer()
        self.fields["projects"] = ProjectSerializer(many=True)
        return super(CollectionSerializer, self).to_representation(instance)

    def get_field_names(self, declared_fields, info):
        expanded_fields = super(CollectionSerializer, self).get_field_names(declared_fields, info)
        if getattr(self.Meta, 'extra_fields', None) and len(self.Meta.extra_fields) > 0:
            return expanded_fields + list(self.Meta.extra_fields)
        else:
            return expanded_fields

    def get_total(self, instance):
        return instance.projects.count()


class CollectionSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Collection
        fields = '__all__'


class ValidateSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Validate
        fields = '__all__'


class ContributeSerializerSimple(serializers.ModelSerializer):
    class Meta:
        model = models.Contribute
        fields = '__all__'
