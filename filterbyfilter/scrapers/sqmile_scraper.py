import json
from datetime import date
from operator import attrgetter
from typing import List, Dict

import requests
from bs4 import BeautifulSoup

from filterbyfilter.scrapers.base_scraper import BaseScraper
from ..coffee import Coffee


class SquareMileScraper(BaseScraper):
    DEFAULT_WEIGHT: int = -1

    def __init__(self) -> None:
        self.URL = "https://shop.squaremilecoffee.com/"

    @property
    def scrape(self) -> List[Coffee]:

        shop_homepage = requests.get(self.URL)
        coffee_urls = self._find_coffee_urls(shop_homepage)

        coffees: List[Coffee] = []
        coffees_dict: Dict = {}

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
                    coffee_price.update(self._get_price_dict(price.text))
            else:
                price_soup = product_soup[0].find_all('span', attrs={'itemprop': 'price'})
                coffee_price.update(self._get_price_dict(price_soup[0].text))

            # Extract tasting notes
            tasting_notes: List[str] = []
            if coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'}):
                tns_soup = coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'})
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
                url=url
            )

            with open('tmp_current_coffee_data.json', 'r') as file:
                json_coffee_data = json.load(file)

            coffee_dict: Dict = {
                coffee_name: {
                    'description': coffee_description,
                    'origin': origin,
                    'altitude': coffee_altitude,
                    'price': coffee_price,
                    'process': process,
                    'tasting_notes': tasting_notes,
                    'url': url,
                }
            }

            coffee_dict[coffee_name].update({'date_added': self._date_added(coffee_dict, json_coffee_data)})

            # self._coffee_writer(coffee_dict)
            coffees_dict.update(coffee_dict)
            coffees.append(current_coffee)

        self._coffee_writer(coffees_dict)

        return coffees

    @staticmethod
    def _coffee_writer(coffee_dict: Dict) -> None:

        """Helper function to write current coffees to a JSON file.

        Parameters
        ----------
        coffee_dict: Dict
            Dictionary of all currently available coffees.

        Returns
        -------
        None
        """
        with open('tmp_current_coffee_data.json', 'w') as write_file:
            json.dump(coffee_dict, write_file, indent=4)

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
        {weight: price}
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
            print(price_str_list)
            raise ValueError('Weight in incorrect format.')

        price = float(price_str_list[1].strip('£'))

        return {weight: price}

    @staticmethod
    def _date_added(current_coffee: Dict, last_coffees: Dict) -> tuple:

        """Helper function for checking the date a given coffee was added.l

        Parameters
        ----------
        current_coffee: Dict
            The coffee to be checked for when it was added to Square Mile.

        last_coffees: Dict
            The JSON document with the results from the previous execution of sqmile_scraper.
            Contains all the coffees available at the last check date.

        Returns
        -------
        date_added_tuple: tuple
            Tuple storing the year, month, and day the coffee was added to Square Mile.

        """
        date_added_tuple = (0, 0, 0)
        attrs = ('tm_year', 'tm_mon', 'tm_mday')
        for key in current_coffee.keys():
            if key in last_coffees.keys():
                if 'date_added' in current_coffee[key].keys():
                    date_added_tuple = current_coffee[key]['date_added']
                else:
                    date_added_tuple = tuple(attrgetter(*attrs)(date.timetuple(date.today())))
            else:
                date_added_tuple = tuple(attrgetter(*attrs)(date.timetuple(date.today())))

        return date_added_tuple
