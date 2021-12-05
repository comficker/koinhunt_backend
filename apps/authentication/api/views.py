import os
import uuid
from rest_framework import views
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.filters import OrderingFilter, SearchFilter
from rest_framework_jwt.settings import api_settings
from rest_framework import status
from rest_framework import viewsets, permissions
from django.db import connection
from django.contrib.auth.models import User
from apps.authentication.api.serializers import UserSerializer
from apps.media.models import Media
from apps.authentication.models import Profile
from apps.base import pagination
from web3 import Web3
from web3.middleware import geth_poa_middleware
from eth_account.messages import defunct_hash_message
from django.contrib.auth.tokens import default_token_generator
from rest_framework_jwt.views import verify_jwt_token

jwt_payload_handler = api_settings.JWT_PAYLOAD_HANDLER
jwt_encode_handler = api_settings.JWT_ENCODE_HANDLER
w3 = Web3(Web3.HTTPProvider(os.getenv('RPC_URL')))
w3.middleware_onion.inject(geth_poa_middleware, layer=0)


class UserViewSet(viewsets.ModelViewSet):
    models = User
    queryset = models.objects.order_by('-id')
    serializer_class = UserSerializer
    permission_classes = permissions.AllowAny,
    pagination_class = pagination.Pagination
    filter_backends = [OrderingFilter, SearchFilter]
    search_fields = ['first_name', 'last_name', 'username']
    lookup_field = 'username'
    lookup_value_regex = '[\w.@+-]+'


class UserExt(views.APIView):
    @api_view(['GET'])
    @permission_classes((IsAuthenticated,))
    def get_request_user(request, format=None):
        return Response(UserSerializer(request.user).data)


@api_view(['POST'])
def auth(request):
    signature = request.data.get('message')
    message_hash = defunct_hash_message(text='KOIN_HUNT_AUTHENTICATION')
    address = w3.eth.account.recoverHash(message_hash, signature=signature)
    if not address:
        return Response(status=status.HTTP_400_BAD_REQUEST)
    else:
        address = address.lower()
    print(address)
    profile, is_created = Profile.objects.get_or_create(
        address=address,
        chain="BSC"
    )
    print(is_created)
    print(profile)
    user = profile.user
    if user is None:
        password = str(uuid.uuid4().hex)[:10]
        user = User.objects.create_user(
            username=address,
            password=password
        )
        profile.user = user
        profile.save()
    payload = jwt_payload_handler(user)
    return Response({
        "address": address,
        "token": jwt_encode_handler(payload),
    })
