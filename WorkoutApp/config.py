from datetime import datetime
from datacalcfunctions import *
from typing import Union

def write_sessions()-> None:
    sessions = db.get_sessions()
    with open('session_log.txt', 'w') as file:
        for _, v in sessions.items():
            date = datetime.fromisoformat(v['date'])
            date_str = datetime.strftime(date, '%b %d, %Y')
            file.write(date_str + '\n')

# def parse_date(iso_date:str ) -> str:
#     """Take date as string and return month 
#     and day in str format (i.e. Jan 01)"""
#     try:
#         date = datetime.fromisoformat(iso_date)
#         return datetime.strftime(date, '%b %d')
#     except ValueError:
#         return iso_date

def parse_date(date: Union[datetime, str], format:str = 'Mon DD' ) -> str:
    """Convert datetime object to string in custom formats"""
    formats = {
        'YYYY-MM-DD' : '%Y-%m-%d',
        'Mon DD' : '%b %d'
}
    
    if isinstance(date, str):
        if date == 'Never':
            return date
    
        try:
            date = datetime.fromisoformat(date)
        except ValueError:
            print('Unsupported string value')

    try:
        date = datetime.strftime(date, formats[format])

    except KeyError:
        formats = '\n'.join(formats.keys())
        print('Invalid date format entered. Valid formats include:')
        print(formats)
    
    return date

    

chart_colors = {   
    'red' : [.8, .35, .35],
    'orange' : [.95, .57, .26],
    'teal' : [0, .7373, .8314],
    'transparent' : [.1294, .1294, .1294],
    'green' : [.5647, .9297, .5647],
    }

data_cards = { # Should this just be a list of dicts rather than a dict of dicts?
    'this_week' : {
        'enabled' : True,
        'title' : 'Sessions This Week',
        'name' : 'THIS_WEEK',
        'calc_function' : calc_this_week,
        'line': True,
    },
    'sessions_per_week' : {
        'enabled' : True,
        'title': 'Average Sessions (per week)',
        'name': 'SESSIONS_PER_WEEK',
        'calc_function' : sessions_per_week,
        'line': True,
    },
    'current_sessions' : {
        'enabled' : True,
       'title': 'Current Streak (sessions)',
        'name': 'CURRENT_SESSIONS',
        'calc_function' : current_sessions,
        'line': False,
    },
    'highest_weeks' : {
        'enabled' : True,
        'title': 'Longest Streak (weeks)',
        'name': 'HIGHEST_WEEKS',
        'calc_function' : highest_weeks,
        'line': False,
    },
    'highest_sessions' : {
        'enabled' : True,
        'title': 'Longest Streak (sessions)',
        'name' : 'HIGHEST_SESSIONS',
        'calc_function' : highest_sessions,
        'line': False,
    }
    }

                

    # DataCard:
    #     title: 'Current Streak (weeks)'
    #     id: current_weeks
    #     name: 'CURRENT_WEEkS'
    #     line: False
    
    