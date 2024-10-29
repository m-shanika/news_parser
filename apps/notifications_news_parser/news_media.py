import traceback
import requests
from apps.notifications_news_parser.notification_service import NotificationService
from apps.models import NewsMedia, Organization
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class NewsMediaFetcher:
    def __init__(self, org: Organization):
        self.org = org
        self.news_url = "https://cmp.wildberries.ru/cmpf/api/twirp/api.LkGateway/GetNews"
        self.news_headers = None

    def get_access_token(self):
        from apps.notifications_news_parser.organization_updater import OrganizationUpdater
        org_updater = OrganizationUpdater(self.org)
        return org_updater.get_access_token()

    def prepare_news_headers(self, access_token):
        self.news_headers = {
            'accept': '*/*',
            'accept-language': 'ru-UZ,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'authorizev3': access_token,
            'cache-control': 'max-age=0',
            'origin': 'https://cmp.wildberries.ru',
            'priority': 'u=1, i',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'x-admin': '0',
            'x-supplier-id-external': self.org.supplier_id,
            'x-supplierid': '0',
            'x-user-id': '0',
        }

    def fetch_news(self):
        try:
            response = requests.post(self.news_url, headers=self.news_headers, json={})
            response.raise_for_status()
            logger.debug(f"Full response: {response.text}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return None

    def extract_news_info(self, response_json):
        if 'news' not in response_json:
            logger.error("Unexpected JSON structure.")
            return []

        news_items = response_json['news']
        news_info = []
        for news_item in news_items:
            publication_date_str = news_item.get("publication_date")
            
            # Преобразуем дату из формата 'дд.мм.гггг' в datetime
            if publication_date_str:
                try:
                    publication_date = datetime.strptime(publication_date_str, "%d.%m.%Y")
                except ValueError:
                    logger.error(f"Ошибка при разборе даты: {publication_date_str}")
                    publication_date = None
            else:
                publication_date = None
            
            news_info.append({
                "id": news_item.get("id"),
                "title": news_item.get("title"),
                "body": news_item.get("body"),
                "publicationDate": publication_date  # Добавляем преобразованную дату
            })

        return news_info

    def get_news(self):
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Не удалось получить access token.")
            return []

        self.prepare_news_headers(access_token)
        response_json = self.fetch_news()
        if response_json:
            news_list = self.extract_news_info(response_json)
            
            # Удаляем новости без даты публикации
            news_list = [news for news in news_list if news['publicationDate'] is not None]
            
            # Сортируем по дате публикации (от старого к новому)
            news_list_sorted = sorted(news_list, key=lambda x: x['publicationDate'])
            
            # Ограничиваем количество новостей до последних 5
            return news_list_sorted[-5:]
        else:
            logger.error("Не удалось получить новости.")
            return []

    def _send_news(self, news_list: list[dict]):
        ns = NotificationService()
        for news in news_list:
            if not NewsMedia.objects.filter(news_id=news['id']).exists():
                try:
                    logger.info(f"Пытаюсь сохранить новость: {news}")
                    ns.send_news_from_wb([news])
                    NewsMedia.objects.create(
                        news_id=news['id'],
                        title=news['title'],
                        body=news['body'],
                        publication_date=news['publicationDate']  # Сохраняем дату публикации в базе данных
                    )
                    logger.info(f"Новость {news['id']} успешно сохранена.")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении новости {news['id']} в базе данных: {e}", exc_info=True)
                    continue

    async def start(self):
        news_list = self.get_news()
        if news_list:
            self._send_news(news_list)
