from dataclasses import dataclass
from datetime import date
from typing import NamedTuple, Union, Callable
import datacalcfunctions as c


@dataclass
class DataCardData:
    name: str
    title: str
    target: int = 3
    start_date_str: str = date.today().isoformat()
    unit: str = 'Sessions'
    circle: bool = False
    

data_card_data = {
    'this_week' : DataCardData(
        name = 'this_week',
        title = 'Sessions This Week',
        start_date_str='',
        unit = '',
        circle = True,
    ),
    'sessions_per_week' : DataCardData(
        name = 'sessions_per_week',
        title = 'Average Weekly Sessions',
        unit = '',
        circle = True,
    ),
    'current' : DataCardData(
        name = 'current',
        title = 'Current Streak',
        start_date_str = '',
    ),
    'longest' : DataCardData(
        name = 'longest',
        title = 'Longest Streak',
    ),
}

calc_functions = {
        'this_week' : c.calc_this_week,
        'sessions_per_week': c.sessions_per_week,
        'current' : {
            'Weeks' : c.current_weeks,
            'Sessions' : c.current_sessions
        },
        'longest' : {
            'Weeks' : c.highest_weeks,
            'Sessions' : c.highest_sessions,
        }
    }

