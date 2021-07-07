from typing import List

import requests
from bs4 import BeautifulSoup

from filterbyfilter.scrapers.base_scraper import BaseScraper
from ..coffee import Coffee


class SquareMileScraper(BaseScraper):

    def __init__(self):
        self.URL = "https://shop.squaremilecoffee.com/"

    @property
    def scrape(self) -> List[Coffee]:

        shop_homepage = requests.get(self.URL)
        coffee_urls = self._find_coffee_urls(shop_homepage)

        coffees: List[Coffee] = []
        for url in coffee_urls:
            coffee_page = requests.get(url)
            coffee_soup = BeautifulSoup(coffee_page.text, 'lxml')

            # extract name
            name_soup = coffee_soup.find_all('meta', attrs={'property': 'og:title'})
            coffee_name = name_soup[0]['content']

            # extract description
            description_soup = coffee_soup.find_all('meta', attrs={'property': 'og:description'})
            coffee_description = description_soup[0]['content']

            # extract origin, process, altitude if there
            info_soup = coffee_soup.find_all('div', attrs={'class': 'sqmile-wysiwyg'})
            origin = []
            process = []
            coffee_altitude = None
            for div in info_soup:
                for p in div.find_all('p'):
                    if 'Country' in p.text:
                        origin.append(p.text)
                    if 'Altitude' in p.text:
                        coffee_altitude = p.text
                    for i in p.find_all('i'):
                        if i.text == 'Process':
                            process.append(p.text)

            # extract price for smallest pack size. Default is 350g
            # but specials like 'Jam' may be less - check description.
            coffee_price = []
            product_soup = coffee_soup.find_all('form', attrs={'action': '/cart/add'})
            if option_soup := product_soup[0].find_all('div', attrs={'id': 'product-variants'}):
                for price in option_soup[0].find_all('option'):
                    coffee_price.append(price.text)
            else:
                price_soup = product_soup[0].find_all('span', attrs={'itemprop': 'price'})
                coffee_price.append(price_soup[0].text)

            # if len(price_soup) == 1:
            #     print('price found')
            #     for item in price_soup:
            #         coffee_price = item.text
            # else:
            #     coffee_price = None

            # for item in price_soup:
            #     coffee_price = item.text

            # extract tasting notes
            tasting_notes: List[str] = []
            if coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'}):
                tns_soup = coffee_soup.find('div', attrs={'class': 'sqm-product-tasting-notes-pp'})
                for note in tns_soup:
                    tasting_notes.extend(note)

            current_coffee = Coffee(coffee_name, coffee_description, origin,
                                    coffee_altitude, coffee_price, process, tasting_notes, url)
            coffees.append(current_coffee)

        return coffees

    @staticmethod
    def _find_coffee_urls(shop_homepage: requests.Response) -> List[str]:

        """Helper function to find and return all required coffee URLs.

        Parameters
        ----------
        shop_homepage: requests.Response
            Webpage containing a brief description of, and links to, all
            available coffees.

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
