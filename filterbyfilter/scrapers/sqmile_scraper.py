from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from filterbyfilter.scrapers.base_scraper import BaseScraper
from ..coffee import Coffee


class SquareMileScraper(BaseScraper):

    DEFAULT_WEIGHT: int = -1

    def __init__(self) -> None:
        self.URL = "https://shop.squaremilecoffee.com/"

    def scrape(self) -> List[Coffee]:

        shop_homepage = requests.get(self.URL)
        coffee_urls = self._find_coffee_urls(shop_homepage)

        coffees: List[Coffee] = []
        for url in coffee_urls:
            coffee_page = requests.get(url)
            coffee_soup = BeautifulSoup(coffee_page.text, 'lxml')

            # Extract name
            name_soup = coffee_soup.find_all('meta', attrs={'property': 'og:title'})
            coffee_name = name_soup[0]['content']

            # Extract description
            description_soup = coffee_soup.find_all('meta', attrs={'property': 'og:description'})
            coffee_description = description_soup[0]['content']

            # Extract origin, process, altitude
            origin = []
            process = []
            coffee_altitude = None
            origin_process_alt_soup = coffee_soup.find_all('div', attrs={'class': 'sqmile-wysiwyg'})
            for div in origin_process_alt_soup:
                for p in div.find_all('p'):
                    if 'Country' in p.text:
                        origin.append(p.text)
                    if 'Altitude' in p.text:
                        coffee_altitude = p.text
                    for i in p.find_all('i'):
                        if i.text == 'Process':
                            process.append(p.text)

            # Extract prices
            coffee_price = {}
            product_soup = coffee_soup.find_all('form', attrs={'action': '/cart/add'})
            if option_soup := product_soup[0].find_all('div', attrs={'id': 'product-variants'}):
                for price in option_soup[0].find_all('option'):
                    # return price dict
                    coffee_price.update(self._get_price_dict(price.text))
            else:
                price_soup = product_soup[0].find_all('span', attrs={'itemprop': 'price'})
                # return price dict
                coffee_price.update(self._get_price_dict(price_soup[0].text))

            # Extract tasting notes
            tasting_notes: List[str] = []
            if coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'}):
                tns_soup = coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'})
                for note in tns_soup:
                    tasting_notes.extend(note)

            current_coffee = Coffee(
                name=coffee_name,
                description=coffee_description,
                origin=origin,
                altitude=coffee_altitude,
                price=coffee_price,
                process=process,
                tasting_notes=tasting_notes,
                url=url
            )

            coffees.append(current_coffee)

        return coffees

    @staticmethod
    def _find_coffee_urls(shop_homepage: requests.Response) -> List[str]:

        """Helper function to find and return all required coffee URLs.

        Parameters
        ----------
        shop_homepage: requests.Response
            Webpage containing a brief description of, and links to, all
            available filter coffees.

        Returns
        -------
        coffee_links: List[str]
            List of URLs pointing to relevant products.
        """

        soup = BeautifulSoup(shop_homepage.content, "lxml")
        filter_products = soup.find_all("article", attrs={"data-show": "filter"})

        coffee_links = []
        for product in filter_products:
            meta_urls = product.find_all('meta', attrs={'itemprop': 'url'})
            product_url = meta_urls[0]['content']

            if not product_url.startswith('https://shop.squaremilecoffee.com/products/'):
                raise ValueError('Link does not point to a coffee.')

            coffee_links.append(product_url)

        return coffee_links

    def _get_price_dict(self, price_str: str) -> Dict[int, float]:
        price_str_list = price_str.split(' - ')

        if len(price_str_list) == 1:
            return {self.DEFAULT_WEIGHT: float(price_str_list[0].strip('£'))}

        if price_str_list[0].endswith('kg'):
            weight = int(float(price_str_list[0].strip('kg')) * 1000)
        elif price_str_list[0].endswith('g'):
            weight = int(price_str_list[0].strip('g'))
        else:
            print(price_str_list)
            raise ValueError('Weight in incorrect format.')

        price = float(price_str_list[1].strip('£'))

        return {weight: price}
