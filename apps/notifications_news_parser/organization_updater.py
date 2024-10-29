import traceback

import requests

from apps.models import Organization

refresh_token_headers = {
    'host': 'seller-auth.wildberries.ru',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'content-type': 'application/json',
    'sec-ch-ua-mobile': '?0',
    'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
    'sec-ch-ua-platform': '"Windows"',
    'accept': '*/*',
    'origin': 'https://seller.wildberries.ru',
    'sec-fetch-site': 'same-site',
    'sec-fetch-mode': 'cors',
    'sec-fetch-dest': 'empty',
    'referer': 'https://seller.wildberries.ru/',
    'accept-language': 'ru-RU,ru;q=0.9,en-US;q=0.8,en;q=0.7',
    'priority': 'u=1, i',
}

fetch_personal_info_headers = {
    'accept': '*/*',
    'accept-language': 'ru-UZ,ru;q=0.9,en-UZ;q=0.8,en-US;q=0.7,en-GB;q=0.6,en;q=0.5',
    'content-type': 'application/json',
    'priority': 'u=1, i',
    'referer': 'https://seller.wildberries.ru/',
    'sec-ch-ua': '"Not)A;Brand";v="99", "Google Chrome";v="127", "Chromium";v="127"',
    'sec-ch-ua-mobile': '?0',
    'sec-ch-ua-platform': '"macOS"',
    'sec-fetch-dest': 'empty',
    'sec-fetch-mode': 'cors',
    'sec-fetch-site': 'same-origin',
    'user-agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/127.0.0.0 Safari/537.36',
}


class OrganizationUpdater:
    refresh_token_url = "https://seller-auth.wildberries.ru/auth/v2/auth/slide-v3"
    fetch_personal_info_url = 'https://seller.wildberries.ru/passport/api/v2/user/personal_data'

    def __init__(self, org: Organization):
        self.org = org

    def get_access_token(self):
        if self._check_if_token_is_valid():
            return self.org.access_token
        access_token = self._refresh_access_token()
        self.org.access_token = access_token
        self.org.save(update_fields=('access_token',))
        return access_token

    def _refresh_access_token(self):
        cookies = {
            'wbx-seller-device-id': self.org.seller_device_id,
            'external-locale': 'ru',
            'wbx-refresh': self.org.refresh_token,
            'wbx-validation-key': self.org.validation_key,
        }
        try:
            response = requests.post(self.refresh_token_url, headers=refresh_token_headers, cookies=cookies)
            if response.status_code == 200:
                response_json = response.json()
                access_token = response_json.get("payload", {}).get("access_token")
                if access_token:
                    print("Токен успешно получен.")
                    return access_token
                else:
                    print("Токен доступа не найден в ответе.")
                    return None
            else:
                print(f"Запрос не удался с кодом состояния: {response.status_code}")
                return None
        except Exception as e:
            traceback.print_exc()
            return None

    def _check_if_token_is_valid(self) -> bool:

        cookies = {
            'wbx-validation-key': self.org.validation_key,
            'external-locale': 'ru',
            'x-supplier-id': self.org.supplier_id,
            'x-supplier-id-external': self.org.supplier_id,
            'upstream-cluster-uuid': 'ru',
            'WBTokenV3': self.org.access_token,
            'locale': 'ru',
        }

        response = requests.get(self.fetch_personal_info_url, cookies=cookies,
                                headers=fetch_personal_info_headers)
        if response.status_code == 200:
            return True
        return False
