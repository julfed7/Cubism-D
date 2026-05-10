import cloudscraper
from bs4 import BeautifulSoup


def get_namemc_skins(username):
    url = f"https://namemc.com/{username}"

    # Создаем объект scraper вместо requests
    scraper = cloudscraper.create_scraper()

    try:
        # Делаем запрос через scraper
        response = scraper.get(url, timeout=10)

        if response.status_code == 403:
            return "Ошибка 403: Доступ все еще заблокирован защитой сайта"

        if response.status_code != 200:
            return f"Ошибка: Код {response.status_code}"

        soup = BeautifulSoup(response.text, "html.parser")
        skins = []

        # Ищем ссылки на скины
        for a in soup.select("a[href^='/skin/']"):
            skin_id = a["href"].split("/")[-1]
            if skin_id and skin_id not in skins:
                skins.append(skin_id)

        return skins

    except Exception as e:
        return f"Ошибка: {e}"
