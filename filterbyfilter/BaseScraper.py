import abc


class BaseScraper(abc.ABC):

    @abc.abstractmethod
    def pull(self):
        raise NotImplementedError('BaseScraper::pull()')

    @abc.abstractmethod
    def scrape(self):
        raise NotImplementedError('BaseScraper::scrape()')
