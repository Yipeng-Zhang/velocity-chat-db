# Importing Sqlite3 Module
import sqlite3


class DbConnector:
    def __init__(self, db_name_list):

        self.sqliteConnection = {}

        for db_name in db_name_list:
            # Making a connection between sqlite3
            file_path = '/home/zha324/Data/{}.sqlite'.format(db_name)
            # print("Path file:", file_path)
            self.sqliteConnection[db_name] = sqlite3.connect(file_path)
            self.sqliteConnection[db_name].text_factory = self.my_text_factory


    def exe_sql(self, db_name, sql):
        try:
            # Creating cursor object using connection object
            cursor = self.sqliteConnection[db_name].cursor()
            
            # executing our sql query
            cursor.execute(sql)
            
            # Return the result from the database
            return cursor.fetchall()
        except Exception as e:
            # Return an error message if there's an exception (wrong SQL)
            print("Error! Wrong SQL: " + str(e))
            return "Error! " + str(e)
        
    def my_text_factory(self, value):
        # Decode the value using a specific encoding (e.g., Latin-1)
        try:
            return value.decode('utf-8')
        except UnicodeDecodeError:
            return value.decode('latin-1')

    def get_table_schema(self, db_name, table_name):
        sql = "SELECT sql FROM sqlite_master WHERE type='table' and name='{}'".format(table_name)
        db_schema = self.exe_sql(db_name, sql)
        return db_schema[0]

