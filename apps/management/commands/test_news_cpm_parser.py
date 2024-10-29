import asyncio
from django.core.management import BaseCommand
from apps.models import Organization
from apps.notifications_news_parser.news_cpm import NewsCPMFetcher  

class Command(BaseCommand):
    help = 'Тестирование NewsCPMFetcher'

    def handle(self, *args, **options):
        try:
            org = Organization.objects.first()
            nf = NewsCPMFetcher(org)
            asyncio.run(nf.start())
        except Organization.DoesNotExist:
            self.stderr.write(self.style.ERROR('Organization with the specified name does not exist.'))
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during NewsCPMFetcher execution: {e}"))
