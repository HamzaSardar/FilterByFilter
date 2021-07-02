from typing import NoReturn


class BaseScraper:

    def pull(self) -> NoReturn:
        raise NotImplementedError('BaseScraper::pull()')

    def scrape(self) -> NoReturn:
        raise NotImplementedError('BaseScraper::scrape()')
