import traceback
import requests
from apps.notifications_news_parser.notification_service import NotificationService
from apps.models import NewsCPM, Organization
import logging

logger = logging.getLogger(__name__)

class NewsCPMFetcher:
    def __init__(self, org: Organization):
        self.org = org
        self.news_url = "https://cmp.wildberries.ru/api/v5/news"
        self.news_headers = None

    def get_access_token(self):
        from apps.notifications_news_parser.organization_updater import OrganizationUpdater
        org_updater = OrganizationUpdater(self.org)
        return org_updater.get_access_token()

    def prepare_news_headers(self, access_token):
        cookies_string = (
            f"wbx-validation-key={self.org.validation_key}; "
            f"external-locale=ru; "
            f"x-supplier-id-external={self.org.supplier_id}; "
        )

        self.news_headers = {
            'accept': '*/*',
            'accept-language': 'ru-UZ,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'authorizev3': access_token,
            'cache-control': 'no-cache',
            'lang': 'ru',
            'priority': 'u=1, i',
            'referer': 'https://cmp.wildberries.ru/campaigns/news',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
            'cookie': cookies_string,
        }

    def fetch_news(self):
        try:
            response = requests.get(self.news_url, headers=self.news_headers)
            response.raise_for_status()
            logger.debug(f"Full response: {response.text}")
            return response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return None

    def extract_news_info(self, response_json):
        if 'items' not in response_json:
            logger.error("Unexpected JSON structure.")
            return []

        news_items = response_json['items']
        news_info = [
            {
                "id": news_item.get("id"),
                "title": news_item.get("title"),
                "body": news_item.get("body"),
                "publicationDate": news_item.get("publicationDate")
            }
            for news_item in news_items
        ]
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
            
            # Сортируем новости по дате публикации (от старого к новому)
            news_list_sorted = sorted(news_list, key=lambda x: x['publicationDate'])
            
            # Берем только последние 5 новостей
            return news_list_sorted[-5:]
        else:
            logger.error("Не удалось получить новости.")
            return []

    def _send_news(self, news_list: list[dict]):
        ns = NotificationService()
        for news in news_list:
            # Проверяем по news_id, чтобы не отправлять уже сохраненные новости
            if not NewsCPM.objects.filter(news_id=news['id']).exists():
                try:
                    logger.info(f"Пытаюсь сохранить новость: {news}")
                    ns.send_news_from_wb([news])
                    NewsCPM.objects.create(
                        news_id=news['id'],
                        title=news['title'],
                        body=news['body'],
                        publication_date=news['publicationDate']
                    )
                    logger.info(f"Новость {news['id']} успешно сохранена.")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении новости {news['id']} в базе данных: {e}", exc_info=True)
                    continue

    async def start(self):
        news_list = self.get_news()
        if news_list:
            self._send_news(news_list)
