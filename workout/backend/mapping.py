from dataclasses import dataclass
import datetime

import matplotlib.dates as mpl_dates
from backend import utils


@dataclass
class DataCardData:
    target: int
    has_start: bool
    unit: str = ''
    start_date_str: str = ''


class WorkoutOptionInfo:

    def __init__(self, id: str, value: dict) -> None:
        self.id: str = id
        self.title: str = value['title']
        self.last_completed: str = utils.parse_date(value['last_completed'])
        self.lift_info_dict: dict[str, int] = value['lifts']
        self.lift_info: str = self._parse_lift_info(value['lifts'])
    

    def _parse_lift_info(self, lift_info: dict) -> str:
        info = []
        for key, value in lift_info.items():
            info.append(f'{value} x {key}')
        return ", ".join(info)


    def __repr__(self):
        return str(vars(self))


class LiftSessionRecord:
    def __init__(self, key: str, value: dict) -> None:
        self.id: str = key
        self.date = utils.parse_date(value['date'])
        self.sets: dict = value['sets']

    def __repr__(self):
        return str(vars(self))


class PlotData:
    
    def __init__(self, data: dict, period: str) -> None:
        self.time_values = []
        self.lift_values = []
        self.xticks = []
        self.xtick_labels = []
        self._parse_data(data)

    def __repr__(self):
        return '\n\n'.join([k+': '+repr(v) for k,v in vars(self).items()])

    def _parse_data(self, data: dict):
        for value in data.values():
            self.time_values.append(
                datetime.datetime.strptime(value['date'], 
                '%Y-%m-%d').date())
            self.lift_values.append(value['weight'])
        self._set_date_format()

    def _set_date_format(self): 
        self.date_format = mpl_dates.DateFormatter('%b %d')   