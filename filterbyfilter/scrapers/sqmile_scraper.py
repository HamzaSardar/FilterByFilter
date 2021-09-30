from typing import List, Dict, Union
from pathlib import Path

import json
import requests
from bs4 import BeautifulSoup

from .base_scraper import BaseScraper
from ..coffee import Coffee


class SquareMileScraper(BaseScraper):
    DEFAULT_WEIGHT: int = -1

    def __init__(self) -> None:

        """SquareMileScraper -- scrapes coffees from Square Mile Coffee Roasters."""

        self.URL = "https://shop.squaremilecoffee.com/"
        self.coffees: List[Coffee] = []

    def scrape(self) -> List[Coffee]:

        """Function to scrape coffee data from Square Mile website.

        Returns
        -------
        List[Coffee]
            A list of all currently available coffees.
        """

        shop_homepage = requests.get(self.URL)
        coffee_urls = self._find_coffee_urls(shop_homepage)

        for url in coffee_urls:
            coffee_page = requests.get(url)
            coffee_soup = BeautifulSoup(coffee_page.text, 'lxml')

            # Extract name
            name_soup = coffee_soup.find_all('meta', attrs={'property': 'og:title'})
            coffee_name = name_soup[0]['content']

            # Extract description
            description_soup = coffee_soup.find_all('meta', attrs={'property': 'og:description'})
            coffee_description = fr"{description_soup[0]['content']}".replace('\u00a0', ' ').replace('\u2019', ' ')

            # Extract origin, process, altitude
            origin = []
            process = []
            coffee_altitude = None
            origin_process_alt_soup = coffee_soup.find_all('div', attrs={'class': 'sqmile-wysiwyg'})
            for div in origin_process_alt_soup:
                for p in div.find_all('p'):
                    if 'Country' in p.text:
                        country = p.text.split('\n')[2]
                        origin.append(country)
                    if 'Altitude' in p.text:
                        altitude = p.text.split('\n')[2]
                        coffee_altitude = altitude
                    for i in p.find_all('i'):
                        if i.text == 'Process':
                            _process = p.text.split('\n')[2]
                            process.append(_process)

            # Extract prices
            coffee_price = {}
            product_soup = coffee_soup.find_all('form', attrs={'action': '/cart/add'})
            if option_soup := product_soup[0].find_all('div', attrs={'id': 'product-variants'}):
                for price in option_soup[0].find_all('option'):
                    coffee_price.update(self._get_price_dict(price.text))
            else:
                price_soup = product_soup[0].find_all('span', attrs={'itemprop': 'price'})
                coffee_price.update(self._get_price_dict(price_soup[0].text))

            # Extract tasting notes
            tasting_notes: List[str] = []
            if tns_soup := coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'}):
                for note in tns_soup:
                    tasting_notes.append(str(note.string))
            for elem in tasting_notes:
                if '/' in elem:
                    tasting_notes.pop(tasting_notes.index(elem))

            current_coffee = Coffee(
                name=coffee_name,
                description=coffee_description,
                origin=origin,
                altitude=coffee_altitude,
                price=coffee_price,
                process=process,
                tasting_notes=tasting_notes,
                url=url,
                is_available=True
            )

            self.coffees.append(current_coffee)

        return self.coffees

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

        """Helper function to extract coffee price from a string.

        Parameters
        ----------
        price_str: str
            Price of coffee as a string, extracted from BeautifulSoup object.

        Returns
        -------
        Dict[int, float]
            Key-value pair, indicating price per package, and weight of package.
        """
        price_str_list = price_str.split(' - ')

        if len(price_str_list) == 1:
            return {self.DEFAULT_WEIGHT: float(price_str_list[0].strip('£'))}

        if price_str_list[0].endswith('kg'):
            weight = int(float(price_str_list[0].strip('kg')) * 1000)
        elif price_str_list[0].endswith('g'):
            weight = int(price_str_list[0].strip('g'))
        else:
            raise ValueError('Weight in incorrect format.')

        price = float(price_str_list[1].strip('£'))

        return {weight: price}

    def amend_json(self, json_file: Union[str, Path], coffees: List[Coffee]) -> None:

        """Function to check coffee availability. Runs after scrape().
        Checks scraped coffees against the JSON document of all coffees.
        Any coffee in the JSON document but not in the list
        of scraped coffees is no longer available.

        Parameters
        ----------
        json_file: object
            The JSON document containing all coffees.
        coffees: List[Coffee]
            List of all coffees obtained by the scrape() method.
        """

        coffee_names = []
        for coffee_elem in coffees:
            coffee_names.append(coffee_elem.name)

        try:
            with open(json_file, 'r') as f_read:
                json_coffee_data = json.load(f_read)
        except FileNotFoundError:
            json_coffee_data = {}

        for coffee in json_coffee_data.keys():
            if coffee not in coffee_names:
                json_coffee_data[coffee].update({'is_available': False})
            else:
                json_coffee_data[coffee].update({'is_available': True})

        with open(json_file, 'w') as f_write:
            json.dump(json_coffee_data, f_write, indent=4)
