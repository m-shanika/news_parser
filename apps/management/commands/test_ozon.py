import asyncio
from django.core.management import BaseCommand
from apps.news_selenium.news_ozon import OzonNewsParser

class Command(BaseCommand):
    help = 'Тестирование OzonNewsParser'

    def handle(self, *args, **options):
        try:
            parser = OzonNewsParser()
            asyncio.run(parser.start())  # Асинхронный запуск метода start
        except Exception as e:
            self.stderr.write(self.style.ERROR(f"Error during OzonNewsParser execution: {e}"))
