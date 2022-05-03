from typing import Union
from datetime import datetime



def parse_date(date: Union[datetime, str], format:str = 'Mon DD' ) -> str:
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