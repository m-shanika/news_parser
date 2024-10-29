from bs4 import BeautifulSoup
import os
import time
import requests
import html
import re

from configs.settings import TELEGRAM_CHANNEL_ID, TELEGRAM_TOKEN

class NotificationService:
    def __init__(self, channel_id: str = TELEGRAM_CHANNEL_ID):
        self.telegram_token = TELEGRAM_TOKEN
        self.channel_id = channel_id
        self.max_message_length = 4096  # Telegram limit

    def send_notifications_from_wb(self, notifications: list[dict]):
        if not notifications:
            return
        self.channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
        for notification in notifications:
            message = f"У вас новое уведомление:\n\n{notification['text']}\n\n<a href='{notification['link']}'>Перейти к уведомлению</a>"
            if message:
                self._send_message(message)
                time.sleep(3)

    def send_photo_with_caption(self, photo_path: str, caption: str):
        """Отправка фото с подписью в Telegram."""
        if not self.telegram_token or not self.channel_id:
            print("Telegram token или Channel ID не определены.")
            return
        
        url = f"https://api.telegram.org/bot{self.telegram_token}/sendPhoto"
        with open(photo_path, 'rb') as photo:
            data = {
                'chat_id': self.channel_id,
                'caption': caption,
                'parse_mode': 'HTML'  # Поддержка HTML для подписи
            }
            files = {
                'photo': photo
            }
            resp = requests.post(url, data=data, files=files)
            print(resp.json())
            
            if resp.status_code == 429:  # Если слишком много запросов
                time.sleep(1)
                return self.send_photo_with_caption(photo_path, caption)

    def send_news_from_wb(self, news_list: list[dict]):
        if not news_list:
            return
        self.channel_id = os.environ.get("TELEGRAM_CHANNEL_ID")
        for news in news_list:
            decoded_body = self._decode_and_correct_links(news['body'])
            body = self.format_for_telegram(decoded_body)
            message = f"У вас новость:\n\n<b>{news['title']}</b>\n\n{body}"
            self._send_message_in_parts(message)

    def format_for_telegram(self, text: str) -> str:
        """Очищаем текст от неподдерживаемых тегов и форматируем его."""
        soup = BeautifulSoup(text, 'html.parser')

        # Разрешенные теги для Telegram
        allowed_tags = ['b', 'i', 'a', 'code', 'pre']

        for tag in soup.find_all(True):  # True находит все теги
            if tag.name not in allowed_tags:
                tag.unwrap()  # Удаляем теги, оставляя текст

        formatted_text = str(soup)
        
        # Экранируем символы для Telegram
        formatted_text = formatted_text.replace('_', '\\_') \
                                       .replace('*', '\\*') \
                                       .replace('[', '\\[') \
                                       .replace(']', '\\]')

        return formatted_text

    def _decode_and_correct_links(self, text: str) -> str:
        decoded_text = html.unescape(text)

        # Преобразование ссылок в формат HTML
        decoded_text = re.sub(
            r'\\u003ca href=\\"(.*?)\\".*?\\u003e(.*?)\\u003c/a\\u003e',
            r'<a href="\1">\2</a>',
            decoded_text
        )

        return decoded_text

    def _send_message_in_parts(self, message: str):
        """Разбиение сообщений на части, если они превышают лимит."""
        if len(message) <= self.max_message_length:
            self._send_message(message)
        else:
            parts = self._split_message(message, self.max_message_length)
            for part in parts:
                self._send_message(part)
                time.sleep(1)  # Задержка между отправками

    def _split_message(self, message: str, max_length: int) -> list[str]:
        """Разбиение сообщения на части по лимиту."""
        words = message.split()
        parts = []
        current_part = ""

        for word in words:
            if len(current_part) + len(word) + 1 > max_length:
                parts.append(current_part)
                current_part = word
            else:
                current_part += (" " if current_part else "") + word

        if current_part:
            parts.append(current_part)

        return parts

    def _send_message(self, message: str) -> None:
        """Отправка текстового сообщения в Telegram с использованием метода sendMessage."""
        url_req = f"https://api.telegram.org/bot{self.telegram_token}/sendMessage"
        data = {
            "chat_id": self.channel_id,
            "text": message,
            "parse_mode": "HTML"
        }
        resp = requests.post(url_req, data=data)
        print(resp.json())
        if resp.status_code == 429:  # Если слишком много запросов
            time.sleep(1)
            return self._send_message(message)
