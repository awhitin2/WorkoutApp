# WorkoutApp
A mobile app to track workouts and log lifts.

- **Languages**: Python, kvlang
- **Persistence layer**: Google Firebase
- **Major Libraries**: Kivy, Kivy Material Design, Matplotlib


This project was undertaken for educational purposes only and is not currently deployable. 

Before deploying, I would need to revise the Firebase interaction functions contained in database.py. These functions currently utilize the Firebase Admin Python SDK, which does not allow controlled access for individual users, and would instead need to use the Firebase Database REST API. I may do this eventually but as of now the project has fulfilled its educational purposes and is no longer a priority. 


# Features
Screenshots coming

## Selection Screen

- Displays any previously creating workouts
- The next scheduled workout floats to the top of the screen and is outlined in orange
- Allows for the creation of new workouts
    - New workout creation dialog has error checking to prevent creating duplicate workouts or incomplete workouts
- Swipe-to-delete behavior to delete existing workouts
- Selecting a workout launches the Session Screen

## Session Screen

- Allows user to log weight/reps for each of the lifts in the selected workout
- Displays a scrolling record of weight/reps for previous sessions going back to the beginning
- Allows users to add additional lifts to a particular workout session
- Data error checking/validation when logging lift info with error dialogs

## Data Screen

- Displays a graph visualizing weight trends for logged lifts. When clicked, launches the interactive Graph Screen
- Displays a number of Data Cards showing:
    - Number of sessions completed this week
    - Average number of sessions per week since a given start date
    - Current sessions streak where weekly target is reached (user can toggle to display result in sessions or number of weeks)
    - Longest session streak since a given start date (user can toggle to display result in sessions or number of weeks)

## Graph Screen

- Displays an interactive graph allowing the user to visualize their results for any given lift for a number of time periods including the last:
    - week
    - month
    - 3 months
    - 6 months
    - year
    - all time

## View Sessions Screen

- Displays a list of all completed sessions including the title of the workout and date of completion. User can click any session to launch the Edit Sessions Screen
- User can swipe to delete an individual session, or delete all sessions
- User can add a session

## Edit Sessions Screen

- Displays the selected session in an editable format where user can:
    - modify the date
    - Add/delete lifts
    - Add/delete/edit any of the rep/weight info

## Schedule Screen

- Allows user to set a schedule using any of the existing workouts
- Drag-and-drop functionality to rearrange workouts
- Swipe-to-delete functionailty to remove workouts
- User is able to indicate the next scheduled workout, which will float to the top of the Selection Screen
- The next scheduled workout is outlined in orange and updates when the workout is completed in the Session Screen