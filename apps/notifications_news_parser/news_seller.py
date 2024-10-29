import traceback
import requests
from apps.models import NewsSeller, Organization
import logging
from datetime import datetime
from apps.notifications_news_parser.notification_service import NotificationService  # Импортируем сервис для отправки

logger = logging.getLogger(__name__)

class NewsSellerFetcher:
    def __init__(self, org: Organization):
        self.org = org
        self.news_url = "https://seller.wildberries.ru/ns/api/portal-news-go/api/v3/news"
        self.news_headers = None
        self.news_cookies = None

    def get_access_token(self):
        """Получаем или обновляем access_token через OrganizationUpdater."""
        from apps.notifications_news_parser.organization_updater import OrganizationUpdater
        org_updater = OrganizationUpdater(self.org)
        access_token = org_updater.get_access_token()  # Проверяем и обновляем токен
        if access_token:
            logger.info("Токен доступа успешно получен или обновлен.")
        else:
            logger.error("Не удалось получить токен доступа.")
        return access_token

    def prepare_news_headers_and_cookies(self):
        """Готовим заголовки и cookies для запроса."""
        access_token = self.get_access_token()

        if not access_token:
            logger.error("Не удалось получить или обновить access_token.")
            return

        # Устанавливаем заголовки
        self.news_headers = {
            'accept': '*/*',
            'accept-language': 'ru-UZ,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6',
            'content-type': 'application/json',
            'priority': 'u=1, i',
            'referer': 'https://seller.wildberries.ru/news-v2',
            'sec-ch-ua': '"Chromium";v="128", "Not;A=Brand";v="24", "Google Chrome";v="128"',
            'sec-ch-ua-mobile': '?0',
            'sec-ch-ua-platform': '"Windows"',
            'sec-fetch-dest': 'empty',
            'sec-fetch-mode': 'cors',
            'sec-fetch-site': 'same-origin',
            'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36',
        }

        # Устанавливаем cookies
        self.news_cookies = {
            'locale': 'ru',
            '_wbauid': '8779805531723925979',
            '___wbu': 'c0a64c79-20ab-47fd-a29c-dbd2879bcef4.1723925980',
            'wbx-validation-key': self.org.validation_key,
            'WBTokenV3': access_token,
            'external-locale': 'ru',
            'x-supplier-id': self.org.supplier_id,
            'x-supplier-id-external': self.org.supplier_id,
            '___wbs': '3ac8e959-db05-42c7-a550-a43cc5e18061.1727133405',
        }

        logger.info(f"Заголовки запроса: {self.news_headers}")
        logger.info(f"Cookies запроса: {self.news_cookies}")

    def fetch_news(self):
        """Запрос на получение новостей (только первая страница)."""
        params = {
            'bookmarks': 'false',
            'newsType': '0',
            'page': '1',  # Берем только первую страницу
            'query': '',
        }
        try:
            response = requests.get(self.news_url, headers=self.news_headers, cookies=self.news_cookies, params=params)
            response.raise_for_status()  # Проверяем статус ответа
            return response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            logger.error(f"Тело ответа: {response.text if response else 'нет ответа'}")
            return None

    def get_news(self):
        """Функция получения и обработки новостей."""
        self.prepare_news_headers_and_cookies()  # Готовим заголовки и куки
        response_json = self.fetch_news()
        if response_json:
            return self.extract_news_info(response_json)
        else:
            logger.error("Не удалось получить новости.")
            return []

    def extract_news_info(self, response_json):
        """Извлечение информации о новостях и сортировка по дате."""
        if 'data' not in response_json or 'content' not in response_json['data']:
            logger.error("Unexpected JSON structure.")
            return []

        news_items = response_json['data']['content']
        news_info = [
            {
                "id": news_item.get("ID"),
                "title": news_item.get("Header"),
                "body": news_item.get("Text"),
                "date": news_item.get("Date")
            }
            for news_item in news_items
        ]

        # Преобразование строки даты в объект datetime для сортировки
        for news in news_info:
            news['parsed_date'] = datetime.strptime(news['date'], '%Y-%m-%dT%H:%M:%S.%f%z')

        # Сортировка новостей по дате от старых к новым
        news_info_sorted = sorted(news_info, key=lambda x: x['parsed_date'])

        return news_info_sorted[-5:]  # Возвращаем последние 5 новостей
    
    def _send_news(self, news_list: list[dict]):
        """Отправка новостей и их сохранение в базу данных."""
        ns = NotificationService()
        for news in news_list:
            if not NewsSeller.objects.filter(news_id=news['id']).exists():
                try:
                    logger.info(f"Пытаюсь сохранить новость: {news}")
                    ns.send_news_from_wb([news])  # Используем существующую функцию для отправки
                    
                    # Преобразование строки даты в объект datetime для сохранения в базу данных
                    news_date = datetime.strptime(news['date'], '%Y-%m-%dT%H:%M:%S.%f%z')
                    
                    # Создание записи в базе данных с полем date
                    NewsSeller.objects.create(
                        news_id=news['id'],
                        title=news['title'],
                        body=news['body'],
                        date=news_date  # Передаем дату для записи в базу данных
                    )
                    logger.info(f"Новость {news['id']} успешно сохранена.")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении новости {news['id']} в базе данных: {e}", exc_info=True)
                    continue


    async def start(self):
        """Запуск процесса получения и отправки новостей."""
        news_list = self.get_news()  # Получаем новости с первой страницы
        if news_list:
            self._send_news(news_list)
