import datetime
import json
import random

from firebase_admin import credentials, initialize_app, db

from backend import database
from backend import datacarddata

SAMPLE_DATABASE_PATH = 'firebase_mngr/full_sample_data.json'
FIREBASE_CRED_PATH = 'firebase_mngr/firebase_admin.json'

def connect_to_firebase():
        cred = credentials.Certificate(FIREBASE_CRED_PATH)
        initialize_app(cred, {
            'databaseURL': 'https://workout-da0a4-default-rtdb.firebaseio.com/'
        })   

def initialize_full_database():
    '''Set all data except dates and then generate dates and update where 
    appropriate so data appears current'''

    with open(SAMPLE_DATABASE_PATH) as file:
        data = json.load(file)
    db.reference().set(data) #Full database except dates
    _set_database_dates()

def _set_database_dates():
    sessions = database.get_sessions(cache = False)
    dates = _generate_dates(len(sessions))
    workout_completion_dates: dict = {} #defaultdict?
    _update_data_card_starts(dates[0])
    for date, (k, v) in zip(dates, sessions.items()):
        workout = v['workout']
        _update_session_date(k, date)
        workout_completion_dates[v['workout']] = date
        for lift in v['lifts']:
            _update_graph_data_date(k, date, lift)
            _update_completed_lift_date(k, date, lift)
    _update_workout_templates_last_completed(workout_completion_dates)

def _update_data_card_starts(start_date:str) -> None:
    names = _get_data_card_names()
    for name in names:
        if name in datacarddata.cards_with_start:
            database.update_data_card(name, 'start_date_str', start_date)


def _get_data_card_names():
    data = db.reference('/data_cards/').get()
    return [k for k, _ in data.items()]

def _generate_dates(num_dates:int):
    dates = []
    today = datetime.date.today()
    current = today
    num_skip_days = int(num_dates/5)

    for i in range(num_dates + num_skip_days):
        current = current - datetime.timedelta(days= random.randint(2, 4))
        dates.append(current)

    #remove a few extra days to decrease consistency
    skip_days = random.sample(range(num_dates), num_skip_days)
    for i in skip_days:
        del dates[i]

    dates = [date.isoformat() for date in dates]
    dates.reverse()

    return dates


def _update_session_date(k, date):
    db.reference(f'sessions/{k}').update({
        'date': date
        })

def _update_graph_data_date(k, date, lift):
    db.reference(f'graph_data/{lift}/{k}').update({
        'date': date
        })

def _update_completed_lift_date(k, date, lift):
    db.reference(f'completed_lifts/{lift}/{k}').update({
        'date': date
        })

def _update_workout_templates_last_completed(completion_dates: dict[str:str]):
    templates = database.get_workout_templates()
    for template in templates:
        if template.title in completion_dates:
            db.reference('workout_templates/'+template.id).update({
                'last_completed': completion_dates[template.title]
            })


def main():
    connect_to_firebase()
    initialize_full_database()
    with open('backend/database_reset_log.txt', 'a') as file:
        file.write(f'Database reset at: {datetime.datetime.now().isoformat()}\n')

if __name__ == '__main__':
    main()