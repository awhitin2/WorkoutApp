import datetime
from dateutil import relativedelta
from typing import Union

from kivy.uix.widget import Widget


def ancestor_finder(child: Widget, ancestor_type: Widget)-> Widget:
    """
    Traverse a widget's parent tree until an ancestor of the given widget 
    class is found.
    """
    parent = child.parent
    while not isinstance(parent, ancestor_type):
        try:
            parent = parent.parent
            if parent == None:
                print(f"{child} has no ancestor of type {ancestor_type}")
        except AttributeError:
            print(f"{child} has no ancestor of type {ancestor_type}")
    return parent


def parse_date(date: Union[datetime.datetime, str], format:str = 'Mon DD' ) -> str:
    """Convert datetime object to string in custom formats"""
    formats = {
        'YYYY-MM-DD' : '%Y-%m-%d',
        'Mon DD' : '%b %d',
        'Day, Mon DD, YYYY' : '%A, %b %d, %Y'
    }
    
    if isinstance(date, str):
        if date == 'Never':
            return date
    
        try:
            date = datetime.datetime.fromisoformat(date)
        except ValueError:
            print('Unsupported string value')

    try:
        date = datetime.datetime.strftime(date, formats[format])

    except KeyError:
        formats = '\n'.join(formats.keys())
        print('Invalid date format entered. Valid formats include:')
        print(formats)
    
    return date

delta = {
    'Week' : relativedelta.relativedelta(weeks=+1),
    'Month' : relativedelta.relativedelta(months=+1),
    '3 Months' : relativedelta.relativedelta(months=+3),
    '6 Months': relativedelta.relativedelta(months=+6),
    'Year' : relativedelta.relativedelta(years=+1),
    }

def get_start(period):
  
    date = datetime.datetime.now()-delta[period]
    date = parse_date(date, 'YYYY-MM-DD')

    return date
