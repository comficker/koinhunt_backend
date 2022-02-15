import os
import requests
from django.core.management.base import BaseCommand, CommandError
from apps.project.models import Token, TokenPrice
from apps.media.models import Media
from apps.authentication.models import Wallet
import json
import datetime


class Command(BaseCommand):

    def handle(self, *args, **options):
        pass
