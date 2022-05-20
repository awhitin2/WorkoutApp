import datetime
from backend import database


if __name__ == '__main__':
    database.initialize_full_database()
    print(f'Database reset at: {datetime.datetime.now().isoformat()}')

