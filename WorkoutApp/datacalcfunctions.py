from datetime import datetime
import database as db


def calc_this_week(data_card)-> int:
    """Calculate the number of sessions completed this week"""
    iso_cal = datetime.now().isocalendar()
    first_of_week_str = datetime.fromisocalendar(year = iso_cal.year, week = iso_cal.week, day = 1)\
                                .isoformat()
    return len(db.get_sessions_since(first_of_week_str))

def current_sessions(data_card)-> int:
    """Calculate current streak of consecutive sessions where weekly target was reached each consecutive week"""
    sessions = db.get_sessions()
    dates = [datetime.fromisoformat(v['date']).isocalendar() for k,v in sessions.items()]
    dates.reverse()
    this_week = datetime.today().isocalendar()[:2]
    streak = 0
    current_streak = 0
    current = None
    for date in dates:
        if not current:
            current = date
        if current[:2] == date[:2]:
            streak += 1
            current_streak += 1
        else:
            if current_streak >= data_card.target and current.week - date.week == 1:
                streak += 1
                current_streak = 1
            else:
                if current[:2] != this_week:
                    return streak
            
        current = date      
        
def current_weeks(data_card)-> int: # Change this (current code is sessions). Return 0 streak if no weeks completed (as opposed to sessions)
    """Calculate current streak of consecutive weeks where weekly target was reached each consecutive week"""
    sessions = db.get_sessions()
    dates = [datetime.fromisoformat(v['date']).isocalendar() for k,v in sessions.items()]
    dates.reverse()
    this_week = datetime.today().isocalendar()
    current_streak = 0
    week_streak = 0
    current_week = None
    for date in dates:
        if not current_week:
            current_week = date
        if current_week[:2] == date[:2]:
            current_streak += 1
        else:
            if current_streak >= data_card.target and current_week.week - date.week == 1:
                week_streak += 1
                current_streak = 1
            else:
                if current_week[:2] != this_week[:2]:
                    return week_streak
                else:
                    current_streak = 1
            
        current_week = date      
        

def sessions_per_week(data_card)-> int:
    '''Calculate the average number of sessions per week since start date'''
    start_date = data_card.start_date_str
    weeks = (datetime.today()-datetime.fromisoformat(start_date)).days//7
    if weeks == 0: return 0

    num_sessions = len(db.get_sessions_since(start_date))
    return round(num_sessions/weeks)
  

def highest_weeks(data_card)-> int:  #This could maybe be improved?
    '''Calculate the highest number of consecutive weeks wherein weekly target was reached since start date'''

    sessions = db.get_sessions_since(data_card.start_date_str)
    longest_streak = 0
    week_streak = 0
    current_streak = 0
    current_week = None
    for _, v in sessions.items():
        iso_cal = datetime.fromisoformat(v['date']).isocalendar()
        if not current_week: 
            current_week = iso_cal
        if iso_cal[:2] == current_week[:2]: 
            current_streak += 1
            if current_streak == data_card.target:
                week_streak += 1
            current_week = iso_cal
        else:
            if week_streak != 0:
                if (iso_cal.week - current_week.week != 1) or (current_streak < data_card.target):
                    if week_streak > longest_streak:
                        longest_streak = week_streak
                    week_streak = 0
            current_streak = 1   
            current_week = iso_cal         
    return max(longest_streak, week_streak)


def highest_sessions(data_card)-> int:  #This could maybe be improved?
    '''Calculate highest number of consecutive sessions where weekly target was reached each consecutive week since start date'''
    
    sessions = db.get_sessions_since(data_card.start_date_str)
    longest_streak = 0
    current_streak = 0
    this_week = 0
    current_week = None
    for _, v in sessions.items():
        iso_cal = datetime.fromisoformat(v['date']).isocalendar()
        if not current_week: 
            current_week = iso_cal
        if iso_cal[:2] == current_week[:2]: 
            current_streak += 1
            this_week += 1
        else:
            if this_week >= data_card.target:
                if iso_cal.week - current_week.week == 1:
                    current_streak += 1
                else:
                    if current_streak > longest_streak:
                        longest_streak = current_streak
                    current_streak = 1
            else:
                if current_streak > longest_streak:
                    longest_streak = current_streak
                current_streak = 1
            this_week = 1
        current_week = iso_cal      

    return max(longest_streak, current_streak)


class FakeCard():
    def __init__(self, target, start_date_str ) -> None:
        self.target = target
        self.start_date_str = start_date_str

functions = {
        'this_week' : calc_this_week,
        'sessions_per_week': sessions_per_week,
        'current' : {
            'Weeks' : current_weeks,
            'Sessions' : current_sessions
        },
        'longest' : {
            'Weeks' : highest_weeks,
            'Sessions' : highest_sessions,
        }
    }


def calculate(data_card):
    if data_card.unit:
        return functions[data_card.name][data_card.unit](data_card)
    return functions[data_card.name](data_card)


# start_date_str = '2022-01-01T00:00:00'
# target = 3

# db.connect_to_firebase()

# print(sessions_per_week(FakeCard(target, start_date_str)))
# print(highest_weeks(FakeCard(target, start_date_str)))
# print(highest_sessions(FakeCard(target, start_date_str)))

# print('finished')