from typing import NoReturn


class BaseScraper:

    def scrape(self) -> NoReturn:
        raise NotImplementedError('BaseScraper::scrape()')
