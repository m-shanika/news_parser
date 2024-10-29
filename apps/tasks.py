import asyncio
import asyncio
from apps.notifications_news_parser.news_media import NewsMediaFetcher
from apps.notifications_news_parser.news_seller import NewsSellerFetcher

from configs.celery import app
from apps.notifications_news_parser.notifiication_parser import NotificationFetcher
from apps.notifications_news_parser.news_cpm import NewsCPMFetcher
from apps.models import Organization, OzonNews
from apps.news_selenium.news_ozon import OzonNewsParser  

@app.task
def check_ozon_news():
    try:
        parser = OzonNewsParser()
        asyncio.run(parser.start())  # Асинхронный запуск метода start
    except Exception as e:
        print(f"Error during OzonNewsParser execution: {e}")

@app.task
def check_notifications():
    try:
        org = Organization.objects.filter(refresh_token__isnull=False).first()
        nc = NotificationFetcher(org)
        asyncio.run(nc.start())
    except Exception as e:
        print(f"Error checking notifications: {e}")

@app.task
def check_news():
    try:
        org = Organization.objects.filter(refresh_token__isnull=False).first()
        nc = NewsCPMFetcher(org)
        asyncio.run(nc.start())
    except Exception as e:
        print(f"Error checking news: {e}")

@app.task
def check_news_media():
    try:
        org = Organization.objects.filter(refresh_token__isnull=False).first()
        nc = NewsMediaFetcher(org)
        asyncio.run(nc.start())
    except Exception as e:
        print(f"Error checking news media: {e}")

@app.task
def check_news_seller():
    try:
        org = Organization.objects.filter(refresh_token__isnull=False).first()
        ns = NewsSellerFetcher(org)
        
        asyncio.run(ns.start())  # Выполняем парсинг новостей, но не отправляем их сразу в Telegram
        
        screenshot_maker = NewsSellerFetcher(org)  # Новый класс для создания скриншотов
        asyncio.run(screenshot_maker.start())
    except Exception as e:
        print(f"Error checking news seller: {e}")
