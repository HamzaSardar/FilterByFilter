from datetime import datetime
from typing import List, Optional


class Coffee:

    def __init__(self,
                 name: str,
                 description: str,
                 origin: List[str],
                 altitude: str,
                 price: List[str],
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

        self.date_added: Optional[datetime] = None
