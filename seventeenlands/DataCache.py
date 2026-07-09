import requests
import time
from datetime import date

from seventeenlands.utils.settings import SETS, FORMATS


class DataCache:
    CACHE: dict = {s: {f: {} for f in FORMATS} for s in SETS}

    @classmethod
    def fetch_data(cls, sets: list[str]) -> None:
        """
        Gets the data the bot uses.
        :param sets: The list of sets to get data for.
        """
        for s in sets:
            cls.CACHE[s] = {f: {} for f in FORMATS}
            for f in FORMATS:
                success = False
                try:
                    print(f'Fetching data for {s} {f}...')
                    response = requests.get(
                        'https://www.17lands.com/card_ratings/data?' +
                        f'expansion={s}&format={f}&time_period=ALL_TIME'
                    )
                    for c in response.json():
                        cls.CACHE[s][f][c['name']] = c
                    success = True
                    print('Success!')
                    time.sleep(2)
                except Exception:
                    print('Failed')

    @classmethod
    def __class_getitem__(cls, set_code) -> dict:
        return cls.CACHE[set_code]
