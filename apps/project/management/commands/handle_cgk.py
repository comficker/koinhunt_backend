import os
from django.core.management.base import BaseCommand
from apps.base.rabbitmq import channel
from utils.coingecko import handle_queue_rabbitmq


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--q')

    def handle(self, *args, **options):
        channel.basic_consume(
            queue=os.getenv(options['q']),
            auto_ack=True,
            on_message_callback=handle_queue_rabbitmq
        )
        channel.start_consuming()
