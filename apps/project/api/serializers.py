from apps.project import models
from rest_framework import serializers
from apps.media.api.serializers import MediaSerializer
from apps.authentication.api.serializers import UserSerializer


class TermSerializer(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)

    class Meta:
        model = models.Term
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["media"] = MediaSerializer()
        return super(TermSerializer, self).to_representation(instance)


class PartnerSerializer(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)

    class Meta:
        model = models.Partner
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["terms"] = TermSerializer(many=True)
        self.fields["media"] = MediaSerializer()
        return super(PartnerSerializer, self).to_representation(instance)


class ProjectSerializer(serializers.ModelSerializer):
    id_string = serializers.CharField(required=False)

    class Meta:
        model = models.Project
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["terms"] = TermSerializer(many=True)
        self.fields["media"] = MediaSerializer()
        self.fields["hunter"] = UserSerializer()
        return super(ProjectSerializer, self).to_representation(instance)


class TokenSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Token
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["chain"] = TermSerializer()
        self.fields["project"] = ProjectSerializer()
        return super(TokenSerializer, self).to_representation(instance)


class EventSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Event
        fields = '__all__'
        extra_fields = []

    def to_representation(self, instance):
        self.fields["project"] = TokenSerializer()
        self.fields["partner"] = PartnerSerializer()
        return super(EventSerializer, self).to_representation(instance)
