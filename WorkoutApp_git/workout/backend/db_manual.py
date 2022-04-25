from datetime import timedelta, date, datetime
import random
from firebase_admin import credentials, initialize_app, db

def connect_to_firebase():
        cred = credentials.Certificate("firebase_admin.json")
        initialize_app(cred, {
            'databaseURL': 'https://workout-da0a4-default-rtdb.firebaseio.com/'
        })   

def get_weights(start, increment):
    weights = []
    weights.append(start)
    current = start
    for i in range(30):
        current = current - random.choice(increment)
        weights.append(current)
    weights.reverse()
    print(weights)
    return weights

def get_dates():
    dates = []
    today = date.today()
    dates.append(today)
    current = today
    for i in range(30):
        current = current - timedelta(days= random.randint(2, 8))
        dates.append(current)
    dates = [parse(date) for date in dates]
    dates.reverse()
    print(dates)
    return dates

def parse(date):
    return datetime.strftime(date, '%b %d')

def register(lift, dates, weights):
    for d, weight in zip(dates, weights):
        register_graph_data(d, lift, weight)

def register_graph_data(date, lift, weight):
        db.reference('/graph_data/'+lift).push(
            {
            date : weight
            })

increment = [0, 0, 0, 2.5]
start = 30
lift = 'Weighted Pull-ups'
connect_to_firebase()
register(lift, get_dates(), get_weights(start, increment))


