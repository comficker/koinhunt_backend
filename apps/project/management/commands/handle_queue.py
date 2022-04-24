from django.core.management.base import BaseCommand
from utils.handle_queue import handle_queue
from threading import Thread


class Command(BaseCommand):
    def add_arguments(self, parser):
        parser.add_argument('--q')

    def handle(self, *args, **options):
        if options['q']:
            handle_queue(options['q'])
        else:
            for topic in [
                "KAFKA_QUEUE_TOKEN",
                "KAFKA_QUEUE_PRICE",
                "KAFKA_QUEUE_PROJECT",
                "KAFKA_QUEUE_EVENT",
            ]:
                if topic:
                    Thread(target=handle_queue, args=(topic,)).start()
