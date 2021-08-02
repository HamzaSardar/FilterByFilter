import json
from datetime import datetime, date
from operator import attrgetter
from pathlib import Path
from typing import Any, List, Optional, Dict, Union


class Coffee:

    def __init__(self,
                 name: str,
                 description: str,
                 origin: List[str],
                 altitude: str,
                 price: Dict[int, float],
                 process: List[str],
                 tasting_notes: List[str],
                 url: str) -> None:

        """Coffee -- contains all relevant product information for a listed coffee.

        Parameters
        ----------
        name: str
            Name of a coffee.
        description: str
            Description provided on product page.
        origin: List[str]
            Country or countries of origin.
        altitude: str
            Altitude the coffee was grown at in MASL.
        price: Dict[int, float]
            Price in GBP per package weight in grams.
        process: List[str]
            Coffee processing method(s).
        tasting_notes: List[str]
            Tasting notes provided on product page.
        url: str
            URL for the coffee product page.
        """

        self.name = name
        self.description = description
        self.origin = origin
        self.altitude = altitude
        self.price = price
        self.process = process
        self.tasting_notes = tasting_notes
        self.url = url
        self.special = len(list(filter(lambda x: x < 0, price.keys()))) > 0

        self.date_added: Optional[datetime] = None

    def write_to_json(self, json_file: Union[str, Path]) -> None:

        """Function to write coffee to a JSON file.

        Parameters
        ----------
        json_file: Union[str, Path]
            Name of file containing previously acquired data.
        """

        if not isinstance(json_file, Path):
            json_file = Path(json_file)

        try:
            with open(json_file, 'r') as f_read:
                json_coffee_data = json.load(f_read)
        except FileNotFoundError:
            json_coffee_data = {}

        coffee_listed = False
        if self.name in json_coffee_data.keys():
            coffee_listed = True

        if not coffee_listed:
            attrs = ('tm_year', 'tm_mon', 'tm_mday')
            self.date_added = tuple(attrgetter(*attrs)(date.timetuple(date.today())))
            json_coffee_data.update({self.name: self._coffee_to_dict()})

        with open(json_file, 'w+') as f_write:
            json.dump(json_coffee_data, f_write, indent=4)

    def _coffee_to_dict(self) -> Dict[str, Any]:

        """Function to convert a Coffee object to a dictionary.

        Returns
        -------
        coffee_dict: Dict[str, Any]
            Dictionary containing all relevant coffee information.
        """

        coffee_dict = {
            'description': self.description,
            'origin': self.origin,
            'altitude': self.altitude,
            'price': self.price,
            'process': self.process,
            'tasting_notes': self.tasting_notes,
            'url': self.url,
            'special': self.special,
            'date_added': self.date_added
        }

        return coffee_dict
