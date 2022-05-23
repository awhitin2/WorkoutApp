import datetime
from backend import database



def main():
    database.initialize_full_database()
    with open('backend/database_reset_log.txt', 'a') as file:
        file.write(f'Database reset at: {datetime.datetime.now().isoformat()}\n')

if __name__ == '__main__':
    main()