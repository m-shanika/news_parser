import asyncio
from django.core.management import BaseCommand
from apps.models import Organization
from apps.notifications_news_parser.news_seller import NewsSellerFetcher
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from selenium.webdriver.chrome.options import Options
import time

class Command(BaseCommand):
    help = 'Тестирование NewsSellerFetcher'

    def handle(self, *args, **options):
        from selenium import webdriver
        from selenium.webdriver.chrome.service import Service
        from webdriver_manager.chrome import ChromeDriverManager
        from selenium.webdriver.chrome.options import Options
        import pickle
        import time
        import random
        import os
        from apps.models import OzonNews
        from apps.notifications_news_parser.notification_service import NotificationService
        import undetected_chromedriver as uc

        class OzonNewsParser:
            def __init__(self):
                self.base_url = "https://seller.ozon.ru"
                self.news_url = f"{self.base_url}/media/news/"
                self.notification_service = NotificationService()
                self.driver = None

            def _setup_driver(self):
                if self.driver is None:
                    options = uc.ChromeOptions()
                    user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/128.0.0.0 Safari/537.36"
                    options.add_argument(f"user-agent={user_agent}")
                    options.add_argument("--headless")
                    options.add_argument("--no-sandbox")
                    options.add_argument("--disable-dev-shm-usage")
                    options.add_argument("--disable-blink-features=AutomationControlled")
                    options.add_argument("--proxy-server=213.230.80.169:8080")

                    self.driver = uc.Chrome(service=Service(ChromeDriverManager().install()), options=options)

                    self.driver.execute_cdp_cmd("Page.addScriptToEvaluateOnNewDocument", {
                        "source": """
                            Object.defineProperty(navigator, 'webdriver', {
                                get: () => undefined
                            });
                        """
                    })

                    # Загрузка cookies из файла
                    with open('cookies.pkl', 'rb') as cookiesfile:
                        cookies = pickle.load(cookiesfile)
                        for cookie in cookies:
                            self.driver.add_cookie(cookie)

                    # Добавление сессий
                    session_cookies = [
                        {"name": "__est__", "value": "MDA0VGg=3GdjxQ=="},
                        {"name": "__gti__", "value": "91681c7a-787e-2922-7176-1e65770335a4"},
                        {"name": "savefrom-helper-extension", "value": "-1802405802"}
                    ]
                    for session_cookie in session_cookies:
                        self.driver.add_cookie(session_cookie)

                return self.driver

            def fetch_news(self, page_limit=1):
                driver = self._setup_driver()
                new_news = []
                if not os.path.exists('screenshots'):
                    os.makedirs('screenshots')
                for page in range(1, page_limit + 1):
                    url = f"{self.news_url}?page={page}"
                    driver.get(url)
                    time.sleep(random.uniform(3, 6))
                    driver.refresh()
                    time.sleep(random.uniform(3, 6))

                    driver.execute_script("window.scrollTo(0, document.body.scrollHeight);")
                    time.sleep(random.uniform(2, 4))

                    news_elements = driver.find_elements(By.CLASS_NAME, "e1a.lb8_2")
                    for news in reversed(news_elements):  # Обрабатываем новости с самого низа (старые новости)
                        try:
                            title_element = news.find_element(By.TAG_NAME, 'h3')
                            title = title_element.text
                            link_element = news.find_element(By.TAG_NAME, 'a')
                            link = self.base_url + link_element.get_attribute('href')

                            if not OzonNews.objects.filter(title=title).exists():
                                OzonNews.objects.create(title=title, link=link)
                                link = link_element.get_attribute('href')  # Получаем ссылку

                                # Открываем новую вкладку и переходим по ссылке
                                driver.execute_script("window.open('{}');".format(link))
                                driver.switch_to.window(driver.window_handles[-1])
                                time.sleep(random.uniform(3, 6))

                                # Проверяем, что страница загрузилась полностью
                                driver.execute_script("return document.readyState == 'complete'")
                                time.sleep(random.uniform(1, 3))

                                # Создаем папку для скриншотов, если её нет
                                screenshot_path = f"screenshots/{title.replace('/', '_')}.png"
                                # Увеличиваем размер окна браузера для захвата всей страницы
                                driver.set_window_size(1920, 1080)
                                scroll_height = driver.execute_script("return document.body.scrollHeight")
                                driver.set_window_size(1920, scroll_height)
                                driver.save_screenshot(screenshot_path)

                                caption = f"Новость Ozon: {title}\nСсылка: {link}"
                                self.notification_service.send_photo_with_caption(screenshot_path, caption)

                                # Закрываем текущую вкладку и возвращаемся к основной
                                driver.close()
                                driver.switch_to.window(driver.window_handles[0])
                                time.sleep(random.uniform(3, 6))
                        except Exception as e:
                            print(f"Ошибка при обработке новости: {e}")

                return new_news

            def close_driver(self):
                if self.driver is not None:
                    self.driver.quit()
                    self.driver = None

            async def start(self):
                self.fetch_news()
                self.close_driver()