import pygame
import cloudscraper
import io


def get_pygame_skin(skin_id):
    # Прямая ссылка на текстуру (файл .png)
    url = f"https://s.namemc.com/i/{skin_id}.png"

    scraper = cloudscraper.create_scraper()

    try:
        response = scraper.get(url, timeout=10)
        if response.status_code == 200:
            # Превращаем байты из интернета в поток данных для pygame
            image_stream = io.BytesIO(response.content)
            skin_surface = pygame.image.load(image_stream)
            return skin_surface
        else:
            print(f"Ошибка загрузки: {response.status_code}")
            return None
    except Exception as e:
        print(f"Ошибка: {e}")
        return None

