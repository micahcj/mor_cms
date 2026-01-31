from threading import Lock
from typing import Collection
from pandas import DataFrame


class LockedRoster:
    def __init__(self) -> None:
        self.lock = Lock()
        self._roster = set()
        self.manual_roster = set()
        self.df_dict: dict[str, DataFrame] = {}

    @property
    def roster(self):
        with self.lock:
            return sorted(self._roster)

    def add(self, value: Collection[str]):
        with self.lock:
            self._roster.update(value)

    def get_roster(self):
        return sorted(self._roster)
