from datetime import datetime
from typing import List, Optional, Dict


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
