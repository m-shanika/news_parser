import asyncio
from django.core.management import BaseCommand

from apps.notifications_news_parser.notifiication_parser import NotificationFetcher
from apps.models import Organization


class Command(BaseCommand):
    help = 'Тестирование NotificationChecker'

    def handle(self, *args, **options):
        try:
            org = Organization.objects.first()
            rt = NotificationFetcher(org)
            asyncio.run(rt.start())
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during NotificationFetcher execution: {e}"))
