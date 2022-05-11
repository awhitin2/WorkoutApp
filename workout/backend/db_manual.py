import itertools
from datetime import timedelta, date, datetime
import random
from firebase_admin import credentials, initialize_app, db

def connect_to_firebase():
        cred = credentials.Certificate("firebase_admin.json")
        initialize_app(cred, {
            'databaseURL': 'https://workout-da0a4-default-rtdb.firebaseio.com/'
        })   


#maps lifts to increments to control how quickly the generated weights increase
weight_generation_info = {
    'Bench Press' : {
        'start': 120,
        'increment' : [0, 0, 2.5]
        },
    'Crunches' : {
        'start': 0,
        'increment' : [0]
        },
    'Curls' : {
        'start': 20,
        'increment' : [0, 0, 0, 2.5]
        },
    'Deadlift' : {
        'start': 130,
        'increment' : [0, 2.5, 5]
        },
    'Leg Raises' : {
        'start': 0,
        'increment' : [0]
        },
    'Shoulder Press' : {
        'start': 80,
        'increment' : [0, 0, 2.5]
        },
    'Squat' : {
        'start': 130,
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
    print(weights)
    return weights

def generate_dates(num_dates:int):
    dates = []
    today = date.today()
    # dates.append(today)
    current = today
    num_skip_days = int(num_dates/5)

    for i in range(num_dates + num_skip_days):
        current = current - timedelta(days= random.randint(2, 4))
        dates.append(current)

    #remove a few extra days to decrease consistency
    skip_days = random.sample(range(num_dates), num_skip_days)
    for i in skip_days:
        del dates[i]

    dates = [date.isoformat() for date in dates]
    dates.reverse()

    return dates

# def parse(date):
#     return datetime.strftime(date, '%b %d')

# def register(lift, dates, weights):
#     for d, weight in zip(dates, weights):
#         register_graph_data(d, lift, weight)

# def register_graph_data(date, lift, weight):
#         db.reference('/graph_data/'+lift).push(
#             {
#             date : weight
#             })

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


def generate_sample_db_session_data(num_sessions):
    #get templates
    #
    dates = generate_dates(num_sessions)
    weight_dict = {lift: generate_weights(lift, num_sessions) for lift in weight_generation_info}

    # for lift in weight_generation_info:
    print('finished')

    pass
 
generate_sample_db_session_data(10)

# if __name__ == '__main__':
        
#     increment = [0, 0, 0, 2.5]
#     start = 2.5
#     lift = 'Weighted Pull-ups'
#     connect_to_firebase()
#     register(lift, get_dates(), get_weights(start, increment))


#Get dates
#Get 
#Generate dates
#Generate increasing lifts
# if not session_screen.session_key:
#             session_screen.session_key = db.register_session(session_screen.title)
#             db.update_last_completed(session_screen.name)

#             if session_screen.workout_info.title == schedule_manager.next_name:
#                 schedule_manager.cycle_next_scheduled()
        
#         db.update_session(session_screen.session_key, self.lift)
#         db.register_completed_lift(session_screen.session_key, self.lift, sets)
#         db.register_graph_data(session_screen.session_key, self.lift, max)
