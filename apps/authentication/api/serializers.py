from rest_framework import serializers
from django.contrib.auth.models import User
from apps.authentication.models import Profile
from rest_auth.registration.serializers import RegisterSerializer


class ProfileSerializer(serializers.ModelSerializer):
    class Meta:
        model = Profile
        fields = ['id', 'media', 'bio', 'nick', 'options', 'extra']

    def to_representation(self, instance):
        return super(ProfileSerializer, self).to_representation(instance)


class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['id', 'first_name', 'last_name', 'username']


class NameRegistrationSerializer(RegisterSerializer):
    def update(self, instance, validated_data):
        pass

    def create(self, validated_data):
        pass

    first_name = serializers.CharField(required=False)
    last_name = serializers.CharField(required=False)

    def custom_signup(self, request, user):
        user.first_name = self.validated_data.get('first_name', '')
        user.last_name = self.validated_data.get('last_name', '')
        user.save(update_fields=['first_name', 'last_name'])
