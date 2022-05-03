
from datetime import datetime, date
from dateutil.relativedelta import relativedelta

from firebase_admin import credentials, initialize_app, db

from kivy.app import App

from backend.datacarddata import DataCardData
from backend import mapping
from backend import utils

sessions = {}


delta = {
    'Week' : relativedelta(weeks=+1),
    'Month' : relativedelta(months=+1),
    '3 Months' : relativedelta(months=+3),
    '6 Months': relativedelta(months=+6),
    'Year' : relativedelta(years=+1),
}

def connect_to_firebase():
        cred = credentials.Certificate("backend/firebase_admin.json")
        initialize_app(cred, {
            'databaseURL': 'https://workout-da0a4-default-rtdb.firebaseio.com/'
        })   

connect_to_firebase()

### GETS ###

def get_scheduled_index():
    return db.reference('schedule/next').get()

def get_schedule()->list[str]:
    return db.reference('schedule/order').get()

def get_schedule_data()->dict:
    return db.reference('schedule').get()


def get_workout_templates() -> list[mapping.WorkoutOptionInfo]:
    data: dict = db.reference('workout_templates').order_by_child('last_completed').get()
    workout_options = []
    for key, value in data.items():
        workout_options.append(mapping.WorkoutOptionInfo(key, value))
    return workout_options

def get_latest_workout_template() -> mapping.WorkoutOptionInfo:
    data: dict = db.reference('workout_templates/').order_by_key().limit_to_last(1).get()
    for key, value in data.items():
        return mapping.WorkoutOptionInfo(key, value)


def get_workout_names() -> list[str]:
    data: dict = db.reference('workout_templates').get() 
    return [value['name'] for value in data.values()]


def get_lifts()-> dict[str, bool]:
    """Returns all lifts entered by user for use in workout templates or workout sessions.
    Format = 'bench press': True """
    return db.reference("/lifts").get()

def get_last_completed_lifts(
                    lift:str, 
                    limit: int = None)\
                    -> list[mapping.LiftSessionRecord]: 

    data: dict = db.reference("/completed_lifts/"+lift)\
                    .order_by_key()\
                    .limit_to_last(limit+1).get()
    if not data:
        return False, None
    
    sessions = [mapping.LiftSessionRecord(key, value) for key, value in data.items()]
    sessions.reverse()
    more = False

    if len(sessions) == limit+1:
        more = True
        _ = sessions.pop()
    
    return more, sessions
    
def get_additional_completed_lifts(
                            lift:str, 
                            start: str, 
                            limit: int)\
                            -> list[mapping.LiftSessionRecord]: 

    data: dict = db.reference("/completed_lifts/"+lift)\
                    .order_by_key()\
                    .end_at(start)\
                    .limit_to_last(limit+2).get()
    if not data:
        return False, None
    del data[start]
    sessions = [mapping.LiftSessionRecord(key, value) for key, value in data.items()]
    sessions.reverse()
    more = False
    if len(sessions) == limit+1:
        more = True
        _ = sessions.pop()
    
    return more, sessions



def get_data_card_data(name:str) -> dict:
    data = db.reference('/data_cards/'+name).get()
    return DataCardData(**data)

def get_sessions():
    if not sessions.get('all_sessions'):
        sessions['all_sessions'] = db.reference('/sessions')\
                                    .order_by_child('date').get()
    return sessions['all_sessions']

def get_sessions_since(start_date: str)->dict:
    if not sessions.get(start_date):
        sessions[start_date] = db.reference('/sessions')\
                                    .order_by_child('date')\
                                    .start_at(start_date).get()
    return sessions[start_date]

def get_lifts():
    return ['Rows', 'Bench Press', 'Squats', 'Deadlift', 'Weighted Pull-ups', 'Shoulder Press']

def get_start(period):
    delta = {
        'Week' : relativedelta(weeks=+1),
        'Month' : relativedelta(months=+1),
        '3 Months' : relativedelta(months=+3),
        '6 Months': relativedelta(months=+6),
        'Year' : relativedelta(years=+1),
    }
    date = datetime.now()-delta[period]

    return utils.parse_date(date, 'YYYY-MM-DD')

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

# connect_to_firebase()
# data = get_plot_data('Rows', 'Month')



# def update_plot_data(lift):
#     ref = db.reference("/graph_data/"+lift)
#     data = PlotData(ref.order_by_key().get())
#     for k, d, w in zip(data.keys, data.time_values, data.lift_values):
#         db.reference("/graph_data/"+lift+'/'+k).set({
#             'date' : d,
#             'weight' : w
#         })


### REGISTRATIONS ###
    
def register_workout_template(data: dict):
    db.reference('/workout_templates').push(
        {
        'last_completed': 'Never',
        'name': data['title'],
        'lifts': data['lifts']
        })

def register_completed_lift(key, lift, sets):
    db.reference(f'completed_lifts/{lift}/{key}').set({
            'date': datetime.now().isoformat(),
            'sets': sets 
            })
        
def register_new_lift(lift):
    db.reference('/lifts').update({
        lift : True
        })

def register_session_manual(m,d):
    db.reference('/sessions').push(
        {
        'date': datetime(2022, m, d).isoformat()
        })

def register_session()->str:
    '''Returns the key generated from the firebase push for use in logging
    the rest of session info. This is done so all info generated from logging a
    session can be easily tracked down and deleted if needed
    '''
    new_post_ref = db.reference('/sessions').push(
        {
        'date': datetime.now().isoformat()
        })
    return new_post_ref.key

def register_graph_data(key: str, lift: str, weight: int)->None:
    db.reference(f'graph_data/{lift}/{key}').set(
        {
        'date': date.today().isoformat(),
        'weight' : weight 
        })

    print("graph data registered")

### UPDATES ###

def update_session(key: str, lift: str):

    db.reference(f'/sessions/{key}/lifts').update(
        {
        lift : True
        })

def update_next_index(next):
    ref = db.reference('schedule')
    ref.update({'next': next})

def update_last_completed(workout):
    db.reference('workout_templates/'+workout).update({
            'last_completed': datetime.now().isoformat()
            })

def update_data_card(name, key, value):
    db.reference('/data_cards/'+name).update({
            key : value
            })

### SETS ###

def set_schedule(schedule: dict):
    db.reference('schedule').set(schedule)

def set_data_card(name, d: dict)->None:
    db.reference('/data_cards/'+name).set(d)

### DELETIONS ###

def delete_template(id: str):
    db.reference(f"/workout_templates/{id}").delete()

if __name__ == '__main__':
    pass

    # connect_to_firebase()
    
    # months =    [2, 2, 3, 3]
    # days =      [26, 28, 1, 4]

    # for m, d in zip(months, days):
    #     register_session_manual(m, d)
    # lift = "Bench Press"




