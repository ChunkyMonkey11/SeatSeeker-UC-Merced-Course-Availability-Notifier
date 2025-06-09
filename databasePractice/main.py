# Importing Sqlite3 Module
import sqlite3
# sqliteConnection is the variable that serves as our connection with the db file 'open_classes' it will be made if it doesn't exist already
sqliteConnection = sqlite3.connect('open_classes')

# c serves as a middleware between the connection with the database and SQL commands to be made.
c = sqliteConnection.cursor()

"""
Goal: 
Create a database table that stores each subject and its attached open courses.
subject : [classes]
primary key can be subject since there is only one subject that contains information ON EVERY COURSE within that subject. 
"""

c.