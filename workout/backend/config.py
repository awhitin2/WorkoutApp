from typing import Union
from datetime import datetime

import backend.datacalcfunctions as calc


chart_colors = {   
    'red' : [.8, .35, .35],
    'orange' : [.95, .57, .26],
    'teal' : [0, .7373, .8314],
    'transparent' : [.1294, .1294, .1294],
    'green' : [.5647, .9297, .5647],
    }

# data_cards = { # Should this just be a list of dicts rather than a dict of dicts?
#     'this_week' : {
#         'enabled' : True,
#         'title' : 'Sessions This Week',
#         'name' : 'THIS_WEEK',
#         'calc_function' : calc.this_week,
#         'line': True,
#     },
#     'sessions_per_week' : {
#         'enabled' : True,
#         'title': 'Average Sessions (per week)',
#         'name': 'SESSIONS_PER_WEEK',
#         'calc_function' : calc.sessions_per_week,
#         'line': True,
#     },
#     'current_sessions' : {
#         'enabled' : True,
#        'title': 'Current Streak (sessions)',
#         'name': 'CURRENT_SESSIONS',
#         'calc_function' : calc.current_sessions,
#         'line': False,
#     },
#     'highest_weeks' : {
#         'enabled' : True,
#         'title': 'Longest Streak (weeks)',
#         'name': 'HIGHEST_WEEKS',
#         'calc_function' : calc.highest_weeks,
#         'line': False,
#     },
#     'highest_sessions' : {
#         'enabled' : True,
#         'title': 'Longest Streak (sessions)',
#         'name' : 'HIGHEST_SESSIONS',
#         'calc_function' : calc.highest_sessions,
#         'line': False,
#     }
#     }

                
