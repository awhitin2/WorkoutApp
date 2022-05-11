
import datetime
import random
import itertools
import json

from dateutil.relativedelta import relativedelta

from firebase_admin import credentials, initialize_app, db

from backend import mapping
from backend import utils

workout_sessions_cache = {} #Cache to avoid multiple database lookups


# delta = {
#     ''''''
#     'Week' : relativedelta(weeks=+1),
#     'Month' : relativedelta(months=+1),
#     '3 Months' : relativedelta(months=+3),
#     '6 Months': relativedelta(months=+6),
#     'Year' : relativedelta(years=+1),
# }

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

def get_workout_names() -> list[str]: #Where is this used?
    data: dict = db.reference('workout_templates').get() 
    workouts:list[str] = [value['name'] for value in data.values()]
    return workouts

def register_workout_template(data: dict): #make register_new_workout_template
    db.reference('/workout_templates').push(
        {
        'last_completed': 'Never',
        'name': data['title'],
        'lifts': data['lifts']
        })

def update_last_completed(workout):
    db.reference('workout_templates/'+workout).update({
            'last_completed': datetime.date.today().isoformat()
            })

def delete_template(id: str):
    db.reference(f"/workout_templates/{id}").delete()

### LIFTS ###

def get_lifts()-> dict[str, bool]:
    """Returns all lifts entered by user for use in workout templates or workout sessions.
    Format = 'bench press': True """
    return db.reference("/lifts").get()

def get_lifts(): #make sure the above one is owrking and then delete this one
    return ['Rows', 'Bench Press', 'Squats', 'Deadlift', 'Weighted Pull-ups', 'Shoulder Press']

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

def get_sessions():
    '''Return all workout sessions from cache if previously cached, 
    else retrive from database and cache for future'''

    if not workout_sessions_cache.get('all_sessions'):
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

def update_data_card(name, key, value):
    db.reference('/data_cards/'+name).update({
            key : value
            })

def set_data_card(name, d: dict)->None: #is this used?
    db.reference('/data_cards/'+name).set(d)

### GRAPH DATA ###
#Probably can/should cache graph data

def get_start(period): #is this used elswehere or just in get_plot_data below?
    #can probably move to utils
    delta = {
        'Week' : relativedelta(weeks=+1),
        'Month' : relativedelta(months=+1),
        '3 Months' : relativedelta(months=+3),
        '6 Months': relativedelta(months=+6),
        'Year' : relativedelta(years=+1),
    }
    date = datetime.datetime.now()-delta[period]
    date = utils.parse_date(date, 'YYYY-MM-DD')

    return date

def get_plot_initialization_info():
    return('Bench Press', '3 Months')

def get_plot_data(lift:str, period: str): #Change this to graph data
    if period == 'All Time':
        data: dict = db.reference("/graph_data/"+lift)\
                    .order_by_key().get()
    else:
        start = get_start(period)
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

### Sessions ###

def get_session_lifts(key:str)->list[str]:
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
#When creating sessions, need a variable that updates each time a specific workout
#is completed. Once the loop ends, that workout needs to have it's last_completed updated
#to match the session date

'''
Constant Nodes:
    data_cards
    lifts
    schedule
Modified Nodes:
    completed_lifts
    graph_data
    workout_templates
    sessions --> make workout_sessions

For each of the four modified nodes, all info except dates will be present. 
Dates will be generated during setup and the relevant nodes updated.
Psuedo-code:
    Generate dates
    Grab sessions and iterate throuh:
    For session in sessions:
        assign date
        grab key
        for lift in session.lifts:
            completed_lifts/lift/key.update(date)
            graph_data/lift/key.update(date)

'''

def initialize_sample_database_info():
    with open('backend/default_sample_data.json') as file:
        data = json.load(file)
    db.reference().set(data)


weight_generation_info = {
    'Bench Press' : {
        'start': 120,
        'increment' : [0, 2.5]
        },
    'Incline Bench' : {
        'start': 100,
        'increment' : [0, 2.5]
        },
    'Shoulder Press' : {
        'start': 80,
        'increment' : [0, 0, 2.5]
        },
    'Crunches' : {
        'start': 0,
        'increment' : [0]
        },
    'Leg Raises' : {
        'start': 0,
        'increment' : [0]
        },
    'Weighted Pull-ups' : {
        'start': 2.5,
        'increment' : [0, 0, 0, 2.5]
        },
    'Curls' : {
        'start': 20,
        'increment' : [0, 0, 0, 2.5]
        },
    'Rows' : {
        'start': 90,
        'increment' : [0, 2.5]
        },
    'Deadlift' : {
        'start': 130,
        'increment' : [0, 2.5, 5]
        },
    'Squat' : {
        'start': 130,
        'increment' : [0,2.5,5]
        },
    'Leg Press' : {
        'start': 160,
        'increment' : [0,2.5,5]
        },
    }

def generate_weights(lift:str, n:int):
    info = weight_generation_info[lift]
    weights = []
    start: int = info['start']
    weights.append(start)
    current = start
    for i in range(n-1):
        current = current + random.choice(info['increment'])
        weights.append(current)
    # weights.reverse()
    print(lift, weights, '\n')
    return weights

def generate_dates(num_dates:int):
    dates = []
    today = datetime.date.today()
    # dates.append(today)
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


def get_sessions():
    return db.reference('/sessions').order_by_child('date').get()

def generate_cycles():
    pass

def register_completed_lifts(sessions:dict, cycles: dict[itertools.cycle])->None:
    '''Takes the result of get_sessions and generate_cycles'''

    for k,v in sessions.items():
        for lift in v['lifts']:
            weight = next(cycles[lift])
            sets = [{'reps': 5, 'weight': weight},{'reps': 5, 'weight': weight},{'reps': 5, 'weight': weight}]
            db.reference(f'completed_lifts/{lift}/{k}').set(
                {
                'date': v['date'],
                'sets' : sets 
                })

def register_graph_data(sessions:dict, cycles: dict[itertools.cycle])->None:
    '''Takes the result of get_sessions and generate_cycles'''

    for k,v in sessions.items():
        for lift in v['lifts']:
            weight = next(cycles[lift])
            sets = [{'reps': 5, 'weight': weight},{'reps': 5, 'weight': weight},{'reps': 5, 'weight': weight}]
            db.reference(f'completed_lifts/{lift}/{k}').set(
                {
                'date': v['date'],
                'weight' : weight 
                })


def register_session(lifts: dict, date: str, workout: str):
    db.reference('sessions').push({
        'date': date,
        'lifts': lifts,
        'workout': workout
    })

def register_sample_sessions(num_sessions):
    templates = get_workout_templates()
    template_cycle = itertools.cycle(templates)
    dates = generate_dates(num_sessions)
    for date in dates:
        template = next(template_cycle)
        workout = template.title
        lifts = {key: True for key in template.lift_info_dict}
        register_session(lifts, date, workout)



def generate_sample_db_session_data(num_sessions):
    register_sample_sessions(num_sessions) 
    
    weight_dict = {lift: generate_weights(lift, num_sessions) for lift in weight_generation_info}

    # for lift in weight_generation_info:
    print('finished')

    pass
 

