import asyncio
from django.core.management import BaseCommand
from apps.models import Organization
from apps.notifications_news_parser.news_media import NewsMediaFetcher  

class Command(BaseCommand):
    help = 'Тестирование NewsMediaFetcher'

    def handle(self, *args, **options):
        try:
            org = Organization.objects.first()
            nf = NewsMediaFetcher(org)
            asyncio.run(nf.start())
        except Organization.DoesNotExist:
            self.stderr.write(self.style.ERROR('Organization with the specified name does not exist.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during NewsMediaFetcher execution: {e}"))
