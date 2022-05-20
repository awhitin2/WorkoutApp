
import datetime
import random
import itertools
import json
from typing import Union

from firebase_admin import credentials, initialize_app, db

from backend import mapping
from backend import utils
from backend import datacarddata


def connect_to_firebase():
        cred = credentials.Certificate("backend/firebase_admin.json")
        initialize_app(cred, {
            'databaseURL': 'https://workout-da0a4-default-rtdb.firebaseio.com/'
        })   

connect_to_firebase()

### SCHEDULE ###

def get_scheduled_index(): #Still in use?
    return db.reference('schedule/next').get()

def get_schedule()->list[str]: #Still in use?
    return db.reference('schedule/order').get()

def get_schedule_data()->dict: #Still in use?
    return db.reference('schedule').get()

def update_next_index(next:int)->None:
    ref = db.reference('schedule')
    ref.update({'next': next})

def set_schedule(schedule: dict)->None:
    db.reference('schedule').set(schedule)

### WORKOUT TEMPLATES ###

def get_workout_templates() -> list[mapping.WorkoutOptionInfo]:
    data: dict = db.reference('workout_templates')\
        .order_by_child('last_completed').get()
    workout_options = [mapping.WorkoutOptionInfo(k, v) for k, v in data.items()]
    # workout_options = []
    # for key, value in data.items():
    #     workout_options.append(mapping.WorkoutOptionInfo(key, value))
    return workout_options

def get_latest_workout_template() -> mapping.WorkoutOptionInfo:
    data: dict = db.reference('workout_templates/')\
        .order_by_key()\
        .limit_to_last(1).get()
    for key, value in data.items(): #better way to do this considering there is on one?
        return mapping.WorkoutOptionInfo(key, value)

def get_workout_names() -> list[str]: #Where is this used? Change to titles?
    data: dict = db.reference('workout_templates').get() 
    workouts:list[str] = [value['title'] for value in data.values()]
    return workouts

def register_workout_template(data: dict): #make register_new_workout_template
    db.reference('/workout_templates').push(
        {
        'last_completed': 'Never',
        'title': data['title'],
        'lifts': data['lifts']
        })

def update_last_completed(key):
    db.reference('workout_templates/'+key).update({
            'last_completed': datetime.date.today().isoformat()
            })

def delete_template(id: str):
    db.reference(f"/workout_templates/{id}").delete()

### LIFTS ###

def get_lifts()-> dict[str, bool]:
    """Returns all lifts entered by user for use in workout templates or workout sessions.
    Format = 'bench press': True """
    return db.reference("/lifts").get()

def register_new_lift(lift):
    db.reference('/lifts').update({
        lift : True
        })

### COMPLETED LIFTS ###

def get_last_completed_lifts(lift:str, limit: int = None)\
    -> list[mapping.LiftSessionRecord]: #How to type hint hte double return here?
    #Can this be combined with get_additional_completed_lifts?
    '''Returns True if there are at least limit +1 completed lifts in the 
    database else False
    Also returns limit # of LiftSessionRecord objects.
    '''

    data: dict = db.reference("/completed_lifts/"+lift)\
        .order_by_key()\
        .limit_to_last(limit+1).get()
    if not data:
        return False, None
    
    sessions = [mapping.LiftSessionRecord(key, value) 
        for key, value in data.items()]
    sessions.reverse()
    more = False

    if len(sessions) == limit+1:
        more = True
        #remove the extra session used to check if even more records exist
        _ = sessions.pop()
    
    return more, sessions
    
def get_additional_completed_lifts(lift:str, start: str, limit: int)\
    -> list[mapping.LiftSessionRecord]: #How to type hint hte double return here?
    '''Accepts and uses a start parameter (a firebase ID str) to check for 
    additional lift records prior to those already retrieved.
    Returns True if there are at least limit +1 additional lift records in the 
    database else False
    Also returns limit # of LiftSessionRecord objects.
    '''

    data: dict = db.reference("/completed_lifts/"+lift)\
                    .order_by_key()\
                    .end_at(start)\
                    .limit_to_last(limit+2).get() 
    if not data:
        return False, None
    del data[start] #Firebase includes the start key so must be removed
    sessions = [mapping.LiftSessionRecord(key, value) for key, value in data.items()]
    sessions.reverse()
    more = False
    if len(sessions) == limit+1:
        more = True
        #remove the extra session used to check if even more records exist
        _ = sessions.pop() 
    
    return more, sessions

def get_lift_session(key: str, lift): #what is this? need better name. In use?
    return db.reference(f'completed_lifts/{lift}/{key}/sets').get()


def register_completed_lift(key, lift, sets, date=None):
    if not date:
        date = datetime.date.today().isoformat()
    db.reference(f'completed_lifts/{lift}/{key}').set({
            'date': date,
            'sets': sets 
            })

def delete_completed_lift(key, lift):
    db.reference(f"completed_lifts/{lift}/{key}").delete()

def delete_all_completed_lifts():
    db.reference(f"completed_lifts").delete()


### DATACARDS ###

def get_data_card_data(name:str) -> dict:
    data = db.reference('/data_cards/'+name).get()
    return mapping.DataCardData(**data)

def update_data_card(name, key, value):
    db.reference('/data_cards/'+name).update({
            key : value
            })

def set_data_card(name, d: dict)->None: #is this used?
    db.reference('/data_cards/'+name).set(d)

### GRAPH DATA ###

#No need to cache here as the plots themselves are cached by the FigureManager.
#i.e. these database methods are called only when new data is required

def get_plot_initialization_info():
    lifts: dict = get_lifts()
    if lifts:
        lift: str = next(iter(lifts))
        return(lift, '3 Months')

def get_plot_data(lift:str, period: str) -> Union[mapping.PlotData, None]: #Change this to graph data
    if period == 'All Time':
        data: dict = db.reference("/graph_data/"+lift)\
                    .order_by_key().get()
    else:
        start = utils.get_start(period)
        data: dict = db.reference("/graph_data/"+lift)\
                    .order_by_child('date')\
                    .start_at(start).get()         
    if data: 
        return mapping.PlotData(data, period)

def register_graph_data(key: str, lift: str, weight: int, date_str: str = None)\
    ->None: #Register_new_graph_data?

    if not date_str:
        date_str = datetime.date.today().isoformat()
    db.reference(f'graph_data/{lift}/{key}').set(
        {
        'date': date_str,
        'weight' : weight 
        })

def delete_graph_data(key, lift):
    db.reference(f"graph_data/{lift}/{key}").delete()

def delete_all_graph_data():
    db.reference(f"graph_data").delete()


### SESSIONS ###

workout_sessions_cache = {} 

def get_sessions(cache: bool = True):
    '''Return all workout sessions from cache if previously cached, 
    else retrive from database and (if cache == True) cache for future'''

    if not cache:
        return db.reference('/sessions').order_by_child('date').get()

    if not 'all_sessions' in workout_sessions_cache:
        workout_sessions_cache['all_sessions'] = db.reference('/sessions')\
                                    .order_by_child('date').get()
    return workout_sessions_cache['all_sessions']

def get_sessions_since(start_date: str)->dict:
    '''Return workout sessions since a start date from cache if previously 
    cached, else retrive from database and cache for future'''

    if not workout_sessions_cache.get(start_date):
        workout_sessions_cache[start_date] = db.reference('/sessions')\
                                    .order_by_child('date')\
                                    .start_at(start_date).get()
    return workout_sessions_cache[start_date]

def get_session_lifts(key:str)->list[str]:
    '''Return a string of the lifts completed in a given session'''
    return [*db.reference(f"sessions/{key}/lifts").get()]

def register_session(workout)->str: #register_new_session? log_new_session?
    '''Returns the key generated from the firebase push for use in logging
    the rest of session info. This is necessary to link all info generated when 
    logging a new session so it can all be found later if needed
    '''
    new_post_ref = db.reference('/sessions').push(
        {
        'date': datetime.date.today().isoformat(),
        'workout': workout
        })
    return new_post_ref.key

def update_session(key: str, lift: str): #add_lift_to_session
    db.reference(f'/sessions/{key}/lifts').update(
        {
        lift : True
        })

def update_session_date_workout(key: str, date: str, workout): #is this being called?
    db.reference(f'/sessions/{key}').update(
        {
        'date' : date,
        'workout' : workout
        })

def delete_session(key):
    db.reference(f"sessions/{key}").delete()

def delete_all_sessions():
    db.reference(f"sessions").delete()


#### Setup

def initialize_full_database():
    '''Set all data except dates and then generate dates and update where 
    appropriate so data appears current'''

    with open('backend/full_sample_data.json') as file:
        data = json.load(file)
    db.reference().set(data) #Full database except dates
    _set_database_dates()

def _set_database_dates():
    sessions = get_sessions(cache = False)
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
            update_data_card(name, 'start_date_str', start_date)


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
    templates = get_workout_templates()
    for template in templates:
        if template.title in completion_dates:
            db.reference('workout_templates/'+template.id).update({
                'last_completed': completion_dates[template.title]
            })
