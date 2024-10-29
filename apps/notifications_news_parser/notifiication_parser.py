import traceback
import requests
from apps.notifications_news_parser.notification_service import NotificationService
from apps.models import Notification, Organization
import logging

logger = logging.getLogger(__name__)

class NotificationFetcher:
    def __init__(self, org: Organization):
        self.org = org
        self.notifications_url = "https://seller-communications.wildberries.ru/ns/notifications/suppliers-portal-eu/notifications/getNotifications"
        self.notification_headers = None

    def get_access_token(self):
        from apps.notifications_news_parser.organization_updater import OrganizationUpdater
        org_updater = OrganizationUpdater(self.org)
        return org_updater.get_access_token()

    def prepare_notification_headers(self, access_token):
        cookies_string = (
            f"wbx-validation-key={self.org.validation_key}; "
            f"external-locale=ru; "
            f"WBTokenV3={access_token}; "
            f"x-supplier-id-external={self.org.supplier_id}; "
        )

        self.notification_headers = {
            "accept": "*/*",
            "accept-language": "ru-UZ,ru-RU;q=0.9,ru;q=0.8,en-US;q=0.7,en;q=0.6",
            "content-type": "application/json",
            "cookie": cookies_string,
            "origin": "https://seller.wildberries.ru",
            "referer": "https://seller.wildberries.ru/",
            "sec-ch-ua": '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
            "sec-ch-ua-mobile": "?0",
            "sec-ch-ua-platform": '"Windows"',
            "sec-fetch-dest": "empty",
            "sec-fetch-mode": "cors",
            "sec-fetch-site": "same-site",
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36",
        }

    def fetch_notifications(self):
        payload = {
            "id": "json-rpc_13",
            "jsonrpc": "2.0",
            "params": {
                "cursor": {"limit": 16, "offset": 0},
                "supplierID": self.org.supplier_id
            }
        }
        try:
            response = requests.post(self.notifications_url, headers=self.notification_headers, json=payload)
            response.raise_for_status()
            return response.json()
        except requests.RequestException as e:
            logger.error(f"HTTP Request failed: {e}")
            return None

    def extract_notifications_info(self, response_json):
        if 'result' not in response_json or 'notifications' not in response_json['result']:
            logger.error("Unexpected JSON structure.")
            return []
        
        notifications = response_json['result']['notifications']
        notifications_info = [
            {
                "id": notification.get("id"),  
                "text": notification.get("text"),
                "link": notification.get("linkData", {}).get("linkHref")
            }
            for notification in notifications
        ]
        return notifications_info

    def get_notifications(self):
        access_token = self.get_access_token()
        if not access_token:
            logger.error("Не удалось получить access token.")
            return []

        self.prepare_notification_headers(access_token)
        response_json = self.fetch_notifications()
        if response_json:
            return self.extract_notifications_info(response_json)
        else:
            logger.error("Не удалось получить уведомления.")
            return []

    def _send_notifications(self, notifications: list[dict]):
        ns = NotificationService()
        for notification in notifications:
            if not Notification.objects.filter(notification_id=notification['id']).exists():
                try:
                    logger.info(f"Пытаюсь сохранить уведомление: {notification}")
                    ns.send_notifications_from_wb([notification])
                    Notification.objects.create(
                        notification_id=notification['id'],
                        text=notification['text'],
                        link=notification['link']
                    )
                    logger.info(f"Уведомление {notification['id']} успешно сохранено.")
                except Exception as e:
                    logger.error(f"Ошибка при сохранении уведомления {notification['id']} в базе данных: {e}", exc_info=True)
                    continue

    async def start(self):
        notifications = self.get_notifications()
        if notifications:
            self._send_notifications(notifications)
