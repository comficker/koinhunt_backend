from rest_framework import serializers
from apps.authentication.models import Wallet


class WalletSerializer(serializers.ModelSerializer):
    class Meta:
        model = Wallet
        fields = ['id', 'media', 'bio', 'nick', 'options']

    def to_representation(self, instance):
        return super(WalletSerializer, self).to_representation(instance)
